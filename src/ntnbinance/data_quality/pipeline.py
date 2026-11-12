"""Idempotent Stage F raw-to-clean orchestration."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final, cast

from ntnbinance.data_contract import SCHEMA_VERSION, QualityFlag
from ntnbinance.data_quality.models import (
    CandleRecord,
    CoverageRecord,
    FeatureCoverageRecord,
    QualityStats,
    QuarantineRecord,
)
from ntnbinance.data_quality.parser import iter_raw_envelopes, parse_candle
from ntnbinance.data_quality.quality import (
    add_missing_bar_flags,
    coverage_by_day,
    feature_coverage_by_day,
    flag_out_of_order,
    reconcile_candles,
    validate_candle,
)
from ntnbinance.data_quality.resample import resample_candles
from ntnbinance.data_quality.storage import publish_parquet

QUALITY_VERSION: Final = "1.1.0"


@dataclass(frozen=True, slots=True)
class PipelineResult:
    run_id: str
    reused: bool
    clean_root: Path
    quarantine_root: Path
    stats: QualityStats
    coverage: tuple[CoverageRecord, ...]
    feature_coverage: tuple[FeatureCoverageRecord, ...]
    raw_dataset_counts: dict[str, int]
    excluded_resample_buckets: dict[str, int]


class DataQualityPipeline:
    """Validate raw observations and publish one immutable clean run."""

    def __init__(self, *, raw_root: Path, clean_root: Path, quarantine_root: Path) -> None:
        self.raw_root = raw_root.resolve()
        self.clean_base = clean_root.resolve()
        self.quarantine_base = quarantine_root.resolve()

    def _run_id(self) -> str:
        manifest = self.raw_root / "manifest.jsonl"
        digest = hashlib.sha256()
        digest.update(manifest.read_bytes())
        digest.update(f"quality={QUALITY_VERSION};schema={SCHEMA_VERSION}".encode())
        return digest.hexdigest()[:16]

    @staticmethod
    def _from_manifest(
        *, run_id: str, clean_root: Path, quarantine_root: Path, data: dict[str, object]
    ) -> PipelineResult:
        stats_raw = data["stats"]
        coverage_raw = data["coverage"]
        feature_coverage_raw = data["feature_coverage"]
        if (
            not isinstance(stats_raw, dict)
            or not isinstance(coverage_raw, list)
            or not isinstance(feature_coverage_raw, list)
        ):
            raise ValueError("published clean manifest is invalid")
        return PipelineResult(
            run_id=run_id,
            reused=True,
            clean_root=clean_root,
            quarantine_root=quarantine_root,
            stats=QualityStats(**cast(dict[str, int], stats_raw)),
            coverage=tuple(CoverageRecord(**item) for item in coverage_raw),
            feature_coverage=tuple(FeatureCoverageRecord(**item) for item in feature_coverage_raw),
            raw_dataset_counts=dict(cast(dict[str, int], data["raw_dataset_counts"])),
            excluded_resample_buckets=dict(cast(dict[str, int], data["excluded_resample_buckets"])),
        )

    def run(self) -> PipelineResult:
        run_id = self._run_id()
        clean_root = (
            self.clean_base / "candles" / f"schema_version={SCHEMA_VERSION}" / f"run_id={run_id}"
        )
        quarantine_root = self.quarantine_base / f"run_id={run_id}"
        manifest_path = clean_root / "manifest.json"
        if manifest_path.is_file():
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return self._from_manifest(
                run_id=run_id,
                clean_root=clean_root,
                quarantine_root=quarantine_root,
                data=data,
            )

        candidates: list[CandleRecord] = []
        quarantine: list[QuarantineRecord] = []
        raw_counts: Counter[str] = Counter()
        feature_observations: list[tuple[str, str, int, int]] = []
        raw_records = 0
        for envelope in iter_raw_envelopes(self.raw_root):
            raw_records += 1
            raw_counts[str(envelope.data.get("dataset", "UNKNOWN"))] += 1
            dataset = envelope.data.get("dataset")
            payload = envelope.data.get("payload")
            if dataset in {"funding_rates", "open_interest"} and isinstance(payload, dict):
                symbol = payload.get("symbol")
                event_time = envelope.data.get("event_time_ms")
                if isinstance(symbol, str) and isinstance(event_time, int):
                    cadence_ms = 28_800_000 if dataset == "funding_rates" else 300_000
                    feature_observations.append((dataset, symbol, event_time, cadence_ms))
            parsed = parse_candle(envelope)
            if isinstance(parsed, CandleRecord):
                candidates.append(parsed)
            elif isinstance(parsed, QuarantineRecord):
                quarantine.append(parsed)

        candidates, out_of_order = flag_out_of_order(candidates)
        clock_skew = sum(
            QualityFlag.CLOCK_SKEW in validate_candle(candidate).quality_flags
            for candidate in candidates
        )
        clean_base, reconciled_quarantine, duplicates, conflicts = reconcile_candles(candidates)
        quarantine.extend(reconciled_quarantine)
        clean_base, missing = add_missing_bar_flags(clean_base)
        resampled_15m, excluded_15m = resample_candles(clean_base, target_interval="15m")
        resampled_1h, excluded_1h = resample_candles(clean_base, target_interval="1h")
        all_clean = [*clean_base, *resampled_15m, *resampled_1h]
        if any(record.has_critical_flag for record in all_clean):
            raise ValueError("critical quality flag reached clean publication")
        coverage = coverage_by_day(all_clean)
        feature_coverage = feature_coverage_by_day(feature_observations)
        stats = QualityStats(
            raw_records=raw_records,
            parsed_candles=len(candidates),
            clean_base_candles=len(clean_base),
            resampled_candles=len(resampled_15m) + len(resampled_1h),
            quarantine_records=len(quarantine),
            duplicate_observations=duplicates,
            source_conflicts=conflicts,
            missing_bars=missing,
            out_of_order_observations=out_of_order,
            clock_skew_observations=clock_skew,
        )
        summary: dict[str, object] = {
            "coverage": [asdict(item) for item in coverage],
            "excluded_resample_buckets": {"15m": excluded_15m, "1h": excluded_1h},
            "feature_coverage": [asdict(item) for item in feature_coverage],
            "quality_version": QUALITY_VERSION,
            "raw_dataset_counts": dict(sorted(raw_counts.items())),
            "run_id": run_id,
            "schema_version": SCHEMA_VERSION,
            "stats": asdict(stats),
        }
        publish_parquet(
            candles=all_clean,
            quarantine=quarantine,
            clean_root=clean_root,
            quarantine_root=quarantine_root,
            summary=summary,
        )
        return PipelineResult(
            run_id=run_id,
            reused=False,
            clean_root=clean_root,
            quarantine_root=quarantine_root,
            stats=stats,
            coverage=tuple(coverage),
            feature_coverage=tuple(feature_coverage),
            raw_dataset_counts=dict(sorted(raw_counts.items())),
            excluded_resample_buckets={"15m": excluded_15m, "1h": excluded_1h},
        )
