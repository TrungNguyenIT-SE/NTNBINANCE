"""Content-addressed Stage G label generation from the Stage F clean run."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import duckdb

from ntnbinance.data_contract import QualityFlag
from ntnbinance.data_quality.models import CandleRecord
from ntnbinance.data_quality.parser import iter_raw_envelopes
from ntnbinance.labels.engine import label_sample
from ntnbinance.labels.models import FundingEvent, LabelConfig, LabelResult

LABEL_ENGINE_VERSION = "1.0.1"


@dataclass(frozen=True, slots=True)
class LabelPipelineResult:
    run_id: str
    reused: bool
    output_root: Path
    sample_count: int
    excluded_windows: int
    distribution: dict[str, int]
    by_symbol: dict[str, dict[str, int]]
    by_date: dict[str, dict[str, int]]
    by_regime: dict[str, dict[str, int]]


def _json_default(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (set, frozenset, tuple)):
        return list(value)
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"cannot serialize {type(value).__name__}")


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def _load_candles(clean_root: Path, interval: str) -> list[CandleRecord]:
    parquet_glob = _sql_path(clean_root / "**" / "*.parquet")
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"""
            SELECT dataset, symbol, interval, epoch_ms(open_time), epoch_ms(close_time),
                   epoch_ms(event_time), epoch_ms(ingested_at), open, high, low, close,
                   volume_base, volume_quote, trade_count, taker_buy_volume_base,
                   taker_buy_volume_quote, is_closed, source, raw_identity, raw_ref,
                   quality_flags
            FROM read_parquet('{parquet_glob}', hive_partitioning=true)
            WHERE dataset = 'trade_klines' AND interval = ?
            ORDER BY symbol, open_time
            """,
            [interval],
        ).fetchall()
    finally:
        connection.close()
    records: list[CandleRecord] = []
    for row in rows:
        flags = frozenset(QualityFlag(value) for value in row[20])
        records.append(
            CandleRecord(
                dataset=str(row[0]),
                symbol=str(row[1]),
                interval=str(row[2]),
                open_time_ms=int(row[3]),
                close_time_ms=int(row[4]),
                event_time_ms=int(row[5]),
                ingested_at=datetime.fromtimestamp(int(row[6]) / 1000, tz=UTC),
                open=Decimal(row[7]),
                high=Decimal(row[8]),
                low=Decimal(row[9]),
                close=Decimal(row[10]),
                volume_base=None if row[11] is None else Decimal(row[11]),
                volume_quote=None if row[12] is None else Decimal(row[12]),
                trade_count=None if row[13] is None else int(row[13]),
                taker_buy_volume_base=None if row[14] is None else Decimal(row[14]),
                taker_buy_volume_quote=None if row[15] is None else Decimal(row[15]),
                is_closed=bool(row[16]),
                source=str(row[17]),
                raw_identity=str(row[18]),
                raw_ref=str(row[19]),
                quality_flags=flags,
            )
        )
    return records


def _load_funding(raw_root: Path) -> list[FundingEvent]:
    events: list[FundingEvent] = []
    for envelope in iter_raw_envelopes(raw_root):
        raw = envelope.data
        if raw.get("dataset") != "funding_rates":
            continue
        payload = raw.get("payload")
        if not isinstance(payload, dict):
            continue
        symbol = payload.get("symbol")
        funding_time = payload.get("fundingTime")
        funding_rate = payload.get("fundingRate")
        identity = raw.get("identity_sha256")
        if (
            isinstance(symbol, str)
            and isinstance(funding_time, int)
            and isinstance(funding_rate, str)
            and isinstance(identity, str)
        ):
            events.append(
                FundingEvent(
                    symbol=symbol,
                    funding_time_ms=funding_time,
                    funding_rate=Decimal(funding_rate),
                    raw_identity=identity,
                )
            )
    return sorted(events, key=lambda event: (event.symbol, event.funding_time_ms))


def _nested_counts(results: list[LabelResult], key: str) -> dict[str, dict[str, int]]:
    groups: dict[str, Counter[str]] = defaultdict(Counter)
    for result in results:
        if key == "symbol":
            group = result.symbol
        elif key == "date":
            group = (
                datetime.fromtimestamp(result.decision_time_ms / 1000, tz=UTC).date().isoformat()
            )
        elif key == "regime":
            group = result.volatility_regime.value
        else:
            raise ValueError("unsupported distribution group")
        groups[group][result.label.value] += 1
    return {group: dict(sorted(counts.items())) for group, counts in sorted(groups.items())}


class LabelPipeline:
    def __init__(
        self,
        *,
        clean_root: Path,
        raw_root: Path,
        output_root: Path,
        config_path: Path,
    ) -> None:
        self.clean_root = clean_root.resolve()
        self.raw_root = raw_root.resolve()
        self.output_base = output_root.resolve()
        self.config_path = config_path.resolve()

    def _run_id(self, config: LabelConfig) -> str:
        digest = hashlib.sha256()
        digest.update((self.clean_root / "manifest.json").read_bytes())
        digest.update(config.canonical_hash.encode("ascii"))
        digest.update(LABEL_ENGINE_VERSION.encode("ascii"))
        return digest.hexdigest()[:16]

    def run(self) -> LabelPipelineResult:
        config = LabelConfig.load(self.config_path)
        run_id = self._run_id(config)
        output = self.output_base / f"label_version={config.version}" / f"run_id={run_id}"
        manifest_path = output / "manifest.json"
        if manifest_path.is_file():
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return LabelPipelineResult(
                run_id=run_id,
                reused=True,
                output_root=output,
                sample_count=int(data["sample_count"]),
                excluded_windows=int(data["excluded_windows"]),
                distribution=dict(data["distribution"]),
                by_symbol=dict(data["by_symbol"]),
                by_date=dict(data["by_date"]),
                by_regime=dict(data["by_regime"]),
            )

        base = _load_candles(self.clean_root, "15m")
        intrabars = _load_candles(self.clean_root, "1m")
        funding = _load_funding(self.raw_root)
        base_by_symbol: dict[str, list[CandleRecord]] = defaultdict(list)
        intra_by_symbol: dict[str, list[CandleRecord]] = defaultdict(list)
        funding_by_symbol: dict[str, list[FundingEvent]] = defaultdict(list)
        for record in base:
            base_by_symbol[record.symbol].append(record)
        for record in intrabars:
            intra_by_symbol[record.symbol].append(record)
        for event in funding:
            funding_by_symbol[event.symbol].append(event)

        results: list[LabelResult] = []
        excluded_windows = 0
        for symbol, candles in sorted(base_by_symbol.items()):
            start = config.atr_window
            stop = len(candles) - config.horizon_bars
            for index in range(start, stop):
                history = candles[index - config.atr_window : index + 1]
                future = candles[index + 1 : index + 1 + config.horizon_bars]
                try:
                    result = label_sample(
                        history=history,
                        future=future,
                        intrabars=intra_by_symbol[symbol],
                        funding_events=funding_by_symbol[symbol],
                        config=config,
                    )
                except ValueError:
                    # Non-contiguous windows are ineligible, never silently repaired.
                    excluded_windows += 1
                    continue
                results.append(result)

        distribution = dict(sorted(Counter(item.label.value for item in results).items()))
        by_symbol = _nested_counts(results, "symbol")
        by_date = _nested_counts(results, "date")
        by_regime = _nested_counts(results, "regime")
        summary: dict[str, Any] = {
            "by_date": by_date,
            "by_regime": by_regime,
            "by_symbol": by_symbol,
            "clean_manifest_sha256": hashlib.sha256(
                (self.clean_root / "manifest.json").read_bytes()
            ).hexdigest(),
            "config_hash": config.canonical_hash,
            "config_version": config.version,
            "distribution": distribution,
            "excluded_windows": excluded_windows,
            "label_engine_version": LABEL_ENGINE_VERSION,
            "run_id": run_id,
            "sample_count": len(results),
        }

        temporary = output.with_name(output.name + ".tmp")
        if output.exists() or temporary.exists():
            raise FileExistsError("label output or temporary publication already exists")
        temporary.mkdir(parents=True)
        try:
            with (temporary / "labels.jsonl").open(
                "w", encoding="utf-8", newline="\n"
            ) as destination:
                for result in results:
                    destination.write(
                        json.dumps(
                            asdict(result),
                            default=_json_default,
                            separators=(",", ":"),
                            sort_keys=True,
                        )
                        + "\n"
                    )
            (temporary / "manifest.json").write_text(
                json.dumps(summary, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            temporary.rename(output)
        except Exception:
            if temporary.exists():
                os.rename(temporary, temporary.with_name(temporary.name + ".failed"))
            raise
        return LabelPipelineResult(
            run_id=run_id,
            reused=False,
            output_root=output,
            sample_count=len(results),
            excluded_windows=excluded_windows,
            distribution=distribution,
            by_symbol=by_symbol,
            by_date=by_date,
            by_regime=by_regime,
        )
