"""Generate immutable purged walk-forward and sealed holdout membership."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from ntnbinance.splits.models import (
    Partition,
    SampleWindow,
    SplitConfig,
    WalkForwardFold,
)

SPLIT_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class SplitPipelineResult:
    manifest_path: Path
    manifest_sha256: str
    reused: bool
    counts: dict[str, int]
    unique_timestamps: int
    folds: int


def _sample_id(label_run_id: str, symbol: str, decision_time_ms: int, config_hash: str) -> str:
    raw = f"{label_run_id}\0{symbol}\0{decision_time_ms}\0{config_hash}"
    return hashlib.sha256(raw.encode()).hexdigest()


def load_sample_windows(labels_root: Path) -> tuple[list[SampleWindow], dict[str, str]]:
    """Read timing and identity only; final-holdout classes are never returned."""

    manifest = json.loads((labels_root / "manifest.json").read_text(encoding="utf-8"))
    label_run_id = str(manifest["run_id"])
    config_hash = str(manifest["config_hash"])
    windows: list[SampleWindow] = []
    development_labels: dict[str, str] = {}
    for line in (labels_root / "labels.jsonl").read_text(encoding="utf-8").splitlines():
        data = json.loads(line)
        symbol = str(data["symbol"])
        decision = int(data["decision_time_ms"])
        sample_id = _sample_id(label_run_id, symbol, decision, config_hash)
        windows.append(
            SampleWindow(
                sample_id=sample_id,
                origin_sample_id=sample_id,
                symbol=symbol,
                decision_time_ms=decision,
                vertical_barrier_time_ms=int(data["vertical_barrier_time_ms"]),
            )
        )
        development_labels[sample_id] = str(data["label"])
    return sorted(
        windows, key=lambda item: (item.decision_time_ms, item.symbol)
    ), development_labels


def _ids_for_times(
    samples_by_time: dict[int, list[SampleWindow]], times: list[int]
) -> tuple[str, ...]:
    return tuple(sample.sample_id for timestamp in times for sample in samples_by_time[timestamp])


def intervals_overlap(left: SampleWindow, right: SampleWindow) -> bool:
    """Treat label windows as half-open [decision, vertical barrier)."""

    return (
        left.decision_time_ms < right.vertical_barrier_time_ms
        and right.decision_time_ms < left.vertical_barrier_time_ms
    )


def assert_no_cross_partition_overlap(left: list[SampleWindow], right: list[SampleWindow]) -> None:
    for first in left:
        for second in right:
            if intervals_overlap(first, second):
                raise ValueError(
                    f"label-window leakage: {first.sample_id} overlaps {second.sample_id}"
                )


def _fraction_count(total: int, fraction: Decimal) -> int:
    return max(1, int(Decimal(total) * fraction + Decimal("0.5")))


def build_split(
    samples: list[SampleWindow], config: SplitConfig
) -> tuple[dict[str, Partition], list[WalkForwardFold], dict[str, Any]]:
    if not samples:
        raise ValueError("cannot split an empty label dataset")
    samples_by_time: dict[int, list[SampleWindow]] = defaultdict(list)
    for sample in samples:
        samples_by_time[sample.decision_time_ms].append(sample)
    times = sorted(samples_by_time)
    symbols = {sample.symbol for sample in samples}
    if any({sample.symbol for sample in group} != symbols for group in samples_by_time.values()):
        raise ValueError("every decision timestamp must contain the same symbol universe")
    if len({sample.sample_id for sample in samples}) != len(samples):
        raise ValueError("sample IDs must be unique")
    if any(
        sample.vertical_barrier_time_ms - sample.decision_time_ms != config.horizon_ms
        for sample in samples
    ):
        raise ValueError("sample label horizon does not match split config")

    validation_count = _fraction_count(len(times), config.validation_fraction)
    test_count = _fraction_count(len(times), config.final_holdout_fraction)
    gap = config.embargo_gap_slots
    test_start = len(times) - test_count
    development_end = test_start - gap
    validation_start = development_end - validation_count
    train_end = validation_start - gap
    if train_end < config.minimum_train_timestamps:
        raise ValueError("not enough timestamps after purge and holdout reservation")

    primary_ranges = {
        Partition.TRAIN: times[:train_end],
        Partition.PURGED_TRAIN_VALIDATION: times[train_end:validation_start],
        Partition.VALIDATION: times[validation_start:development_end],
        Partition.EMBARGO_VALIDATION_TEST: times[development_end:test_start],
        Partition.FINAL_HOLDOUT: times[test_start:],
    }
    assignments: dict[str, Partition] = {}
    for partition, selected_times in primary_ranges.items():
        for sample_id in _ids_for_times(samples_by_time, selected_times):
            assignments[sample_id] = partition

    by_id = {sample.sample_id: sample for sample in samples}
    assert_no_cross_partition_overlap(
        [by_id[item] for item in _ids_for_times(samples_by_time, primary_ranges[Partition.TRAIN])],
        [
            by_id[item]
            for item in _ids_for_times(samples_by_time, primary_ranges[Partition.VALIDATION])
        ],
    )
    assert_no_cross_partition_overlap(
        [
            by_id[item]
            for item in _ids_for_times(samples_by_time, primary_ranges[Partition.VALIDATION])
        ],
        [
            by_id[item]
            for item in _ids_for_times(samples_by_time, primary_ranges[Partition.FINAL_HOLDOUT])
        ],
    )

    folds: list[WalkForwardFold] = []
    validation_end = development_end - validation_count * (config.walk_forward_folds - 1)
    for fold_index in range(1, config.walk_forward_folds + 1):
        validation_start_fold = validation_end - validation_count
        train_end_fold = validation_start_fold - gap
        if train_end_fold < config.minimum_train_timestamps:
            raise ValueError("walk-forward fold violates minimum train window")
        folds.append(
            WalkForwardFold(
                fold=fold_index,
                train_ids=_ids_for_times(samples_by_time, times[:train_end_fold]),
                purged_ids=_ids_for_times(
                    samples_by_time, times[train_end_fold:validation_start_fold]
                ),
                validation_ids=_ids_for_times(
                    samples_by_time, times[validation_start_fold:validation_end]
                ),
            )
        )
        validation_end += validation_count

    boundary_a = times[validation_start] - times[train_end - 1]
    boundary_b = times[test_start] - times[development_end - 1]
    embargo_required_ms = config.embargo_minutes * 60_000
    audit = {
        "decision_gap_train_validation_ms": boundary_a,
        "decision_gap_validation_holdout_ms": boundary_b,
        "embargo_required_ms": embargo_required_ms,
        "symbol_universe": sorted(symbols),
        "unique_timestamps": len(times),
    }
    if min(boundary_a, boundary_b) < embargo_required_ms:
        raise ValueError("primary split boundary is shorter than the required embargo")
    return assignments, folds, audit


class SplitPipeline:
    def __init__(
        self,
        *,
        labels_root: Path,
        config_path: Path,
        manifest_path: Path,
    ) -> None:
        self.labels_root = labels_root.resolve()
        self.config_path = config_path.resolve()
        self.manifest_path = manifest_path.resolve()

    def run(self) -> SplitPipelineResult:
        config = SplitConfig.load(self.config_path)
        samples, labels = load_sample_windows(self.labels_root)
        assignments, folds, audit = build_split(samples, config)
        label_manifest_bytes = (self.labels_root / "manifest.json").read_bytes()
        label_jsonl_hash = hashlib.sha256(
            (self.labels_root / "labels.jsonl").read_bytes()
        ).hexdigest()
        by_id = {sample.sample_id: sample for sample in samples}
        counts = dict(
            sorted(Counter(partition.value for partition in assignments.values()).items())
        )
        development_distribution: dict[str, dict[str, int]] = {}
        for partition in (Partition.TRAIN, Partition.VALIDATION):
            partition_counts = Counter(
                labels[sample_id]
                for sample_id, assigned in assignments.items()
                if assigned is partition
            )
            development_distribution[partition.value] = dict(sorted(partition_counts.items()))
        holdout_ids = sorted(
            sample_id
            for sample_id, partition in assignments.items()
            if partition is Partition.FINAL_HOLDOUT
        )
        holdout_hash = hashlib.sha256("\n".join(holdout_ids).encode()).hexdigest()
        manifest: dict[str, Any] = {
            "assignments": {
                sample_id: {
                    "decision_time_ms": by_id[sample_id].decision_time_ms,
                    "origin_sample_id": sample_id,
                    "partition": partition.value,
                    "symbol": by_id[sample_id].symbol,
                    "vertical_barrier_time_ms": by_id[sample_id].vertical_barrier_time_ms,
                }
                for sample_id, partition in sorted(assignments.items())
            },
            "audit": audit,
            "config": asdict(config),
            "config_hash": config.canonical_hash,
            "counts": counts,
            "development_distribution": development_distribution,
            "final_holdout": {
                "authorized_role": config.final_holdout_authorized_role,
                "first_open_stage": config.final_holdout_open_stage,
                "membership_sha256": holdout_hash,
                "opened": False,
                "status": "SEALED",
            },
            "label_jsonl_sha256": label_jsonl_hash,
            "label_manifest_sha256": hashlib.sha256(label_manifest_bytes).hexdigest(),
            "source_label_run_id": json.loads(label_manifest_bytes)["run_id"],
            "split_engine_version": SPLIT_ENGINE_VERSION,
            "split_version": config.version,
            "walk_forward_folds": [asdict(fold) for fold in folds],
        }
        encoded = (
            json.dumps(manifest, default=str, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        )
        digest = hashlib.sha256(encoded).hexdigest()
        if self.manifest_path.exists():
            if self.manifest_path.read_bytes() != encoded:
                raise FileExistsError("locked split manifest differs from regenerated split")
            return SplitPipelineResult(
                manifest_path=self.manifest_path,
                manifest_sha256=digest,
                reused=True,
                counts=counts,
                unique_timestamps=int(audit["unique_timestamps"]),
                folds=len(folds),
            )
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.manifest_path.with_suffix(self.manifest_path.suffix + ".tmp")
        temporary.write_bytes(encoded)
        temporary.replace(self.manifest_path)
        checksum_path = self.manifest_path.with_suffix(".sha256")
        checksum_path.write_text(
            f"{digest}  {self.manifest_path.name}\n", encoding="ascii", newline="\n"
        )
        return SplitPipelineResult(
            manifest_path=self.manifest_path,
            manifest_sha256=digest,
            reused=False,
            counts=counts,
            unique_timestamps=int(audit["unique_timestamps"]),
            folds=len(folds),
        )
