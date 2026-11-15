"""Deterministic point-in-time numeric feature engine v2."""

from __future__ import annotations

import math
from decimal import Decimal
from itertools import pairwise

from ntnbinance.features.models import FeatureCandle, FeatureInput, FeatureVector
from ntnbinance.features.registry import FEATURE_NAMES, FEATURE_VERSION

ZERO = Decimal(0)
ONE = Decimal(1)


def _visible(
    records: tuple[FeatureCandle, ...], *, decision_time_ms: int, dataset: str, interval: str
) -> tuple[FeatureCandle, ...]:
    selected = tuple(
        sorted(
            (
                item
                for item in records
                if item.is_closed
                and item.event_time_ms < decision_time_ms
                and item.close_time_ms < decision_time_ms
                and item.dataset == dataset
                and item.interval == interval
            ),
            key=lambda item: item.close_time_ms,
        )
    )
    times = tuple(item.close_time_ms for item in selected)
    if len(times) != len(set(times)):
        raise ValueError(f"duplicate point-in-time records for {dataset}/{interval}")
    return selected


def _validate_candle(item: FeatureCandle, symbol: str) -> None:
    if item.symbol != symbol or any(
        value <= 0 for value in (item.open, item.high, item.low, item.close)
    ):
        raise ValueError("candle symbol/price is invalid")
    if not item.low <= min(item.open, item.close) <= max(item.open, item.close) <= item.high:
        raise ValueError("invalid OHLC invariant")


def _ratio(current: Decimal, previous: Decimal) -> Decimal:
    if previous == 0:
        raise ValueError("price denominator must be positive")
    return current / previous - ONE


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("mean requires observations")
    return sum(values, ZERO) / Decimal(len(values))


def _population_sd(values: tuple[Decimal, ...]) -> Decimal:
    average = _mean(values)
    variance = _mean(tuple((value - average) ** 2 for value in values))
    return variance.sqrt()


def _returns(candles: tuple[FeatureCandle, ...], count: int) -> tuple[Decimal, ...]:
    selected = candles[-(count + 1) :]
    return tuple(_ratio(current.close, previous.close) for previous, current in pairwise(selected))


def _aligned_record(
    records: tuple[FeatureCandle, ...], close_time_ms: int, name: str
) -> FeatureCandle:
    matches = tuple(item for item in records if item.close_time_ms == close_time_ms)
    if len(matches) != 1:
        raise ValueError(f"missing or duplicate aligned {name} candle")
    return matches[0]


def _neutral_ratio(current: Decimal, history: tuple[Decimal, ...]) -> Decimal:
    average = _mean(history)
    return ZERO if average == 0 else current / average - ONE


def build_feature_vector(data: FeatureInput) -> FeatureVector:
    if data.symbol not in {"BTCUSDT", "ETHUSDT"} or data.decision_time_ms <= 0:
        raise ValueError("unsupported symbol or decision time")
    trade = _visible(
        data.trade_15m,
        decision_time_ms=data.decision_time_ms,
        dataset="trade_klines",
        interval="15m",
    )
    hourly = _visible(
        data.trade_1h, decision_time_ms=data.decision_time_ms, dataset="trade_klines", interval="1h"
    )
    mark = _visible(
        data.mark_15m,
        decision_time_ms=data.decision_time_ms,
        dataset="mark_price_klines",
        interval="15m",
    )
    index = _visible(
        data.index_15m,
        decision_time_ms=data.decision_time_ms,
        dataset="index_price_klines",
        interval="15m",
    )
    if len(trade) < 20 or len(hourly) < 4:
        raise ValueError("insufficient point-in-time candle history")
    for item in (*trade[-20:], *hourly[-4:], *mark[-1:], *index[-1:]):
        _validate_candle(item, data.symbol)
    latest = trade[-1]
    volumes = tuple(item.volume_base for item in trade[-20:])
    takers = tuple(item.taker_buy_volume_base for item in trade[-20:])
    counts = tuple(item.trade_count for item in trade[-20:])
    if any(value is None for value in (*volumes, *takers, *counts)):
        raise ValueError("required volume/taker/trade-count observation is missing")
    typed_volumes = tuple(value for value in volumes if value is not None)
    typed_takers = tuple(value for value in takers if value is not None)
    typed_counts = tuple(Decimal(value) for value in counts if value is not None)
    if any(value < 0 for value in (*typed_volumes, *typed_takers, *typed_counts)):
        raise ValueError("volume/taker/trade-count must be non-negative")
    if any(taker > volume for taker, volume in zip(typed_takers, typed_volumes, strict=True)):
        raise ValueError("taker-buy volume exceeds total volume")

    true_ranges = tuple(
        max(
            current.high - current.low,
            abs(current.high - previous.close),
            abs(current.low - previous.close),
        )
        for previous, current in zip(trade[-15:-1], trade[-14:], strict=True)
    )
    atr_ratio = _mean(true_ranges) / latest.close
    returns_4 = _returns(trade, 4)
    returns_16 = _returns(trade, 16)
    volume_mean = _mean(typed_volumes)
    volume_sd = _population_sd(typed_volumes)
    taker_ratio = ZERO if typed_volumes[-1] == 0 else typed_takers[-1] / typed_volumes[-1]
    mark_record = _aligned_record(mark, latest.close_time_ms, "mark")
    index_record = _aligned_record(index, latest.close_time_ms, "index")
    values_decimal = (
        _ratio(trade[-1].close, trade[-2].close),
        _ratio(trade[-1].close, trade[-5].close),
        _ratio(trade[-1].close, trade[-17].close),
        _population_sd(returns_4),
        _population_sd(returns_16),
        atr_ratio,
        (latest.high - latest.low) / latest.close,
        (latest.close - latest.open) / latest.close,
        (latest.high - max(latest.open, latest.close)) / latest.close,
        (min(latest.open, latest.close) - latest.low) / latest.close,
        _ratio(hourly[-1].close, hourly[-2].close),
        _ratio(hourly[-1].close, hourly[-4].close) / Decimal(3),
        ZERO if atr_ratio == 0 else _ratio(trade[-1].close, trade[-5].close) / atr_ratio,
        _neutral_ratio(typed_volumes[-1], typed_volumes[-4:-1]),
        ZERO if volume_sd == 0 else (typed_volumes[-1] - volume_mean) / volume_sd,
        taker_ratio,
        _neutral_ratio(typed_counts[-1], typed_counts[-4:-1]),
        _ratio(mark_record.close, latest.close),
        _ratio(index_record.close, latest.close),
        ONE if data.symbol == "ETHUSDT" else ZERO,
    )
    values = tuple(float(value) for value in values_decimal)
    if len(values) != len(FEATURE_NAMES) or not all(math.isfinite(value) for value in values):
        raise ValueError("feature vector contains invalid values")
    used = (*trade[-20:], *hourly[-4:], mark_record, index_record)
    lineage = tuple(sorted({(item.dataset, item.event_time_ms) for item in used}))
    max_event_time = max(event_time for _, event_time in lineage)
    if max_event_time >= data.decision_time_ms:
        raise AssertionError("point-in-time lineage breached decision boundary")
    return FeatureVector(
        version=FEATURE_VERSION,
        symbol=data.symbol,
        decision_time_ms=data.decision_time_ms,
        names=FEATURE_NAMES,
        values=values,
        max_event_time_ms=max_event_time,
        lineage=lineage,
    )
