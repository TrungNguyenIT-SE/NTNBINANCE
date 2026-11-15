"""Locked feature-set v2 registry metadata."""

from __future__ import annotations

from dataclasses import dataclass

FEATURE_VERSION = "2.0.0"


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    name: str
    formula: str
    window: str
    source: str
    timestamp_rule: str
    missing_rule: str


def _definition(
    name: str, formula: str, window: str, source: str, missing_rule: str
) -> FeatureDefinition:
    return FeatureDefinition(
        name=name,
        formula=formula,
        window=window,
        source=source,
        timestamp_rule="closed record with event_time_ms < decision_time_ms",
        missing_rule=missing_rule,
    )


FEATURE_REGISTRY = (
    _definition("return_15m_1", "close[t]/close[t-1]-1", "2 bars / 15m", "trade 15m", "reject"),
    _definition("return_15m_4", "close[t]/close[t-4]-1", "5 bars / 15m", "trade 15m", "reject"),
    _definition("return_15m_16", "close[t]/close[t-16]-1", "17 bars / 15m", "trade 15m", "reject"),
    _definition(
        "realized_volatility_4", "population SD of 4 returns", "5 bars / 15m", "trade 15m", "reject"
    ),
    _definition(
        "realized_volatility_16",
        "population SD of 16 returns",
        "17 bars / 15m",
        "trade 15m",
        "reject",
    ),
    _definition("atr_ratio_14", "SMA(TR,14)/close[t]", "15 bars / 15m", "trade 15m", "reject"),
    _definition("range_ratio_15m", "(high-low)/close", "1 bar / 15m", "trade 15m", "reject"),
    _definition("body_ratio_15m", "(close-open)/close", "1 bar / 15m", "trade 15m", "reject"),
    _definition(
        "upper_wick_ratio_15m", "(high-max(open,close))/close", "1 bar / 15m", "trade 15m", "reject"
    ),
    _definition(
        "lower_wick_ratio_15m", "(min(open,close)-low)/close", "1 bar / 15m", "trade 15m", "reject"
    ),
    _definition("trend_1h_1", "close[t]/close[t-1]-1", "2 bars / 1h", "trade 1h", "reject"),
    _definition("trend_1h_3", "(close[t]/close[t-3]-1)/3", "4 bars / 1h", "trade 1h", "reject"),
    _definition(
        "trigger_15m_atr", "return_15m_4/atr_ratio_14", "15 bars / 15m", "trade 15m", "reject"
    ),
    _definition(
        "volume_ratio_4",
        "volume[t]/mean(volume[t-3:t])-1",
        "4 bars / 15m",
        "trade 15m",
        "zero if denominator zero",
    ),
    _definition(
        "volume_zscore_20",
        "(volume[t]-mean20)/population_sd20",
        "20 bars / 15m",
        "trade 15m",
        "zero if SD zero",
    ),
    _definition(
        "taker_buy_ratio",
        "taker_buy_base/volume_base",
        "1 bar / 15m",
        "trade 15m",
        "zero if volume zero",
    ),
    _definition(
        "trade_count_ratio_4",
        "count[t]/mean(count[t-3:t])-1",
        "4 bars / 15m",
        "trade 15m",
        "zero if denominator zero",
    ),
    _definition(
        "mark_trade_basis",
        "mark_close/trade_close-1",
        "aligned 15m",
        "mark + trade",
        "reject if unaligned",
    ),
    _definition(
        "index_trade_basis",
        "index_close/trade_close-1",
        "aligned 15m",
        "index + trade",
        "reject if unaligned",
    ),
    _definition(
        "symbol_is_eth",
        "1 for ETHUSDT else 0",
        "static",
        "declared symbol",
        "reject unsupported symbol",
    ),
)

FEATURE_NAMES = tuple(item.name for item in FEATURE_REGISTRY)
