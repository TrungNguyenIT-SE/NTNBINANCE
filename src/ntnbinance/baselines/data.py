"""Point-in-time feature assembly with a fail-closed final-holdout boundary."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import duckdb

from ntnbinance.baselines.models import FEATURE_NAMES, BaselineSample
from ntnbinance.labels.models import Label, LabelReason
from ntnbinance.splits.models import Partition


def sample_id(label_run_id: str, symbol: str, decision_time_ms: int, config_hash: str) -> str:
    payload = f"{label_run_id}\0{symbol}\0{decision_time_ms}\0{config_hash}"
    return hashlib.sha256(payload.encode()).hexdigest()


_IDENTITY_PATTERNS = {
    "config_hash": re.compile(r'"config_hash":"([0-9a-f]{64})"'),
    "decision_time_ms": re.compile(r'"decision_time_ms":(\d+)'),
    "symbol": re.compile(r'"symbol":"([A-Z0-9]+)"'),
}


def _identity_from_line(line: str) -> tuple[str, int, str]:
    """Read only non-target identity fields before the partition guard runs."""

    matches = {name: pattern.search(line) for name, pattern in _IDENTITY_PATTERNS.items()}
    if any(match is None for match in matches.values()):
        raise ValueError("label row identity is malformed")
    config_match = matches["config_hash"]
    decision_match = matches["decision_time_ms"]
    symbol_match = matches["symbol"]
    assert config_match is not None
    assert decision_match is not None
    assert symbol_match is not None
    return symbol_match.group(1), int(decision_match.group(1)), config_match.group(1)


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def _load_candles(clean_root: Path) -> dict[tuple[str, str, str], list[dict[str, float | int]]]:
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"""
            SELECT dataset, symbol, interval, epoch_ms(close_time), open, high, low, close,
                   volume_base, taker_buy_volume_base
            FROM read_parquet('{_sql_path(clean_root / "**" / "*.parquet")}',
                              hive_partitioning=true)
            WHERE interval IN ('15m', '1h') AND is_closed
            ORDER BY dataset, symbol, interval, close_time
            """
        ).fetchall()
    finally:
        connection.close()
    groups: dict[tuple[str, str, str], list[dict[str, float | int]]] = defaultdict(list)
    for row in rows:
        groups[(str(row[0]), str(row[1]), str(row[2]))].append(
            {
                "time": int(row[3]),
                "open": float(row[4]),
                "high": float(row[5]),
                "low": float(row[6]),
                "close": float(row[7]),
                "volume": 0.0 if row[8] is None else float(row[8]),
                "taker": 0.0 if row[9] is None else float(row[9]),
            }
        )
    return groups


def _closed_before(
    records: list[dict[str, float | int]], timestamp_ms: int
) -> list[dict[str, float | int]]:
    return [record for record in records if int(record["time"]) < timestamp_ms]


def _ratio(current: float, previous: float) -> float:
    return 0.0 if previous == 0 else current / previous - 1.0


def _features(
    groups: dict[tuple[str, str, str], list[dict[str, float | int]]],
    symbol: str,
    decision_time_ms: int,
) -> tuple[float, ...]:
    trade = _closed_before(groups[("trade_klines", symbol, "15m")], decision_time_ms)
    hourly = _closed_before(groups[("trade_klines", symbol, "1h")], decision_time_ms)
    mark = _closed_before(groups[("mark_price_klines", symbol, "15m")], decision_time_ms)
    index = _closed_before(groups[("index_price_klines", symbol, "15m")], decision_time_ms)
    if len(trade) < 15 or len(hourly) < 3 or not mark or not index:
        raise ValueError(f"insufficient point-in-time history for {symbol} at {decision_time_ms}")
    closes = [float(item["close"]) for item in trade]
    last = trade[-1]
    true_ranges: list[float] = []
    for previous, current in zip(trade[-15:-1], trade[-14:], strict=True):
        previous_close = float(previous["close"])
        true_ranges.append(
            max(
                float(current["high"]) - float(current["low"]),
                abs(float(current["high"]) - previous_close),
                abs(float(current["low"]) - previous_close),
            )
        )
    atr_ratio = sum(true_ranges) / len(true_ranges) / closes[-1]
    return_indices = range(len(closes) - 3, len(closes))
    short_returns = [_ratio(closes[index], closes[index - 1]) for index in return_indices]
    mean_return = sum(short_returns) / len(short_returns)
    volatility = math.sqrt(
        sum((value - mean_return) ** 2 for value in short_returns) / len(short_returns)
    )
    volumes = [float(item["volume"]) for item in trade[-4:]]
    average_volume = sum(volumes[:-1]) / 3
    hour_closes = [float(item["close"]) for item in hourly]
    close = closes[-1]
    volume = float(last["volume"])
    values = (
        _ratio(closes[-1], closes[-2]),
        _ratio(closes[-1], closes[-5]),
        _ratio(hour_closes[-1], hour_closes[-2]),
        _ratio(hour_closes[-1], hour_closes[-3]) / 2,
        atr_ratio,
        volatility,
        (float(last["high"]) - float(last["low"])) / close,
        (close - float(last["open"])) / close,
        _ratio(volume, average_volume),
        0.0 if volume == 0 else float(last["taker"]) / volume,
        _ratio(float(mark[-1]["close"]), close),
        _ratio(float(index[-1]["close"]), close),
        1.0 if symbol == "ETHUSDT" else 0.0,
    )
    if len(values) != len(FEATURE_NAMES) or not all(math.isfinite(value) for value in values):
        raise ValueError("invalid feature vector")
    return values


def load_development_samples(
    *,
    split_path: Path,
    labels_path: Path,
    clean_root: Path,
    label_run_id: str,
    execution_cost: float,
) -> tuple[list[BaselineSample], int]:
    """Load TRAIN/VALIDATION only; never deserialize target fields for final holdout."""

    manifest = json.loads(split_path.read_text(encoding="utf-8"))
    assignments = manifest["assignments"]
    groups = _load_candles(clean_root)
    samples: list[BaselineSample] = []
    sealed_rows = 0
    with labels_path.open(encoding="utf-8") as source:
        for line in source:
            identity_symbol, identity_decision, identity_config = _identity_from_line(line)
            identifier = sample_id(
                label_run_id, identity_symbol, identity_decision, identity_config
            )
            assignment = assignments.get(identifier)
            if assignment is None:
                raise ValueError("label row is absent from locked split manifest")
            partition = Partition(assignment["partition"])
            if partition is Partition.FINAL_HOLDOUT:
                sealed_rows += 1
                continue
            if partition is not Partition.TRAIN and partition is not Partition.VALIDATION:
                continue
            raw: dict[str, Any] = json.loads(line)
            symbol = str(raw["symbol"])
            decision = int(raw["decision_time_ms"])
            vertical = int(raw["vertical_barrier_time_ms"])
            trade = _closed_before(groups[("trade_klines", symbol, "15m")], vertical + 1)
            if not trade:
                raise ValueError("vertical close is unavailable")
            samples.append(
                BaselineSample(
                    sample_id=identifier,
                    partition=partition,
                    symbol=symbol,
                    decision_time_ms=decision,
                    vertical_barrier_time_ms=vertical,
                    label=Label(raw["label"]),
                    reason=LabelReason(raw["reason"]),
                    reference_price=float(raw["reference_price"]),
                    upper_barrier=float(raw["upper_barrier"]),
                    lower_barrier=float(raw["lower_barrier"]),
                    barrier_time_ms=(
                        None if raw["barrier_time_ms"] is None else int(raw["barrier_time_ms"])
                    ),
                    execution_cost=execution_cost,
                    funding_cost=float(raw["funding_cost"]),
                    vertical_close=float(trade[-1]["close"]),
                    features=_features(groups, symbol, decision),
                )
            )
    return sorted(samples, key=lambda item: (item.decision_time_ms, item.symbol)), sealed_rows
