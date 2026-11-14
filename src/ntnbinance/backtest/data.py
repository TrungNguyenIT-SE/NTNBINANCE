"""Label-blind validation input assembly from the locked split and clean market data."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import duckdb

from ntnbinance.backtest.models import BacktestInput, MinuteCandle
from ntnbinance.baselines.data import build_features, load_feature_candles
from ntnbinance.baselines.models import FEATURE_NAMES
from ntnbinance.labels.models import LabelConfig, VolatilityRegime
from ntnbinance.labels.pipeline import load_funding_events
from ntnbinance.splits.models import Partition


def _sql_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "''")


def _load_minutes(clean_root: Path) -> dict[str, list[MinuteCandle]]:
    connection = duckdb.connect(":memory:")
    try:
        rows = connection.execute(
            f"""
            SELECT symbol, epoch_ms(open_time), epoch_ms(close_time), open, high, low, close,
                   volume_base, quality_flags
            FROM read_parquet('{_sql_path(clean_root / "**" / "*.parquet")}',
                              hive_partitioning=true)
            WHERE dataset = 'trade_klines' AND interval = '1m' AND is_closed
            ORDER BY symbol, open_time
            """
        ).fetchall()
    finally:
        connection.close()
    grouped: dict[str, list[MinuteCandle]] = defaultdict(list)
    for row in rows:
        flags = tuple(row[8])
        if flags:
            continue
        grouped[str(row[0])].append(
            MinuteCandle(
                symbol=str(row[0]),
                open_time_ms=int(row[1]),
                close_time_ms=int(row[2]),
                open=Decimal(row[3]),
                high=Decimal(row[4]),
                low=Decimal(row[5]),
                close=Decimal(row[6]),
                volume_base=Decimal(row[7]),
            )
        )
    return grouped


def _regime(atr_ratio: Decimal, config: LabelConfig) -> VolatilityRegime:
    if atr_ratio < config.low_volatility_atr_ratio:
        return VolatilityRegime.LOW
    if atr_ratio < config.high_volatility_atr_ratio:
        return VolatilityRegime.NORMAL
    return VolatilityRegime.HIGH


def load_validation_inputs(
    *,
    split_path: Path,
    clean_root: Path,
    raw_root: Path,
    label_config: LabelConfig,
) -> list[BacktestInput]:
    """Build VALIDATION cases without opening any label JSONL or FINAL_HOLDOUT target."""

    manifest = json.loads(split_path.read_text(encoding="utf-8"))
    assignments = manifest["assignments"]
    validation = [
        (sample_id, item)
        for sample_id, item in assignments.items()
        if Partition(item["partition"]) is Partition.VALIDATION
    ]
    feature_candles = load_feature_candles(clean_root)
    minutes = _load_minutes(clean_root)
    funding = load_funding_events(raw_root)
    funding_by_symbol = {
        symbol: tuple(event for event in funding if event.symbol == symbol)
        for symbol in {str(item["symbol"]) for _, item in validation}
    }
    results: list[BacktestInput] = []
    atr_index = FEATURE_NAMES.index("atr_ratio_14")
    for identifier, assignment in validation:
        symbol = str(assignment["symbol"])
        decision = int(assignment["decision_time_ms"])
        vertical = int(assignment["vertical_barrier_time_ms"])
        features = build_features(feature_candles, symbol, decision)
        history = [
            candle
            for candle in feature_candles[("trade_klines", symbol, "15m")]
            if int(candle["time"]) < decision
        ]
        if not history:
            raise ValueError("decision reference candle is unavailable")
        reference = Decimal(str(history[-1]["close"]))
        atr_ratio = Decimal(str(features[atr_index]))
        case_minutes = tuple(
            candle
            for candle in minutes[symbol]
            if candle.open_time_ms >= decision and candle.close_time_ms < vertical
        )
        expected = label_config.horizon_bars * 15
        if len(case_minutes) != expected:
            raise ValueError(
                f"{identifier} has {len(case_minutes)} quality-passing minutes; expected {expected}"
            )
        results.append(
            BacktestInput(
                sample_id=identifier,
                symbol=symbol,
                decision_time_ms=decision,
                vertical_barrier_time_ms=vertical,
                reference_price=reference,
                atr=atr_ratio * reference,
                regime=_regime(atr_ratio, label_config),
                features=features,
                candles=case_minutes,
                funding_events=funding_by_symbol[symbol],
            )
        )
    return sorted(results, key=lambda item: (item.decision_time_ms, item.symbol))


def utc_month(timestamp_ms: int) -> str:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=UTC).strftime("%Y-%m")
