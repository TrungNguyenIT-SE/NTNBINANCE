from __future__ import annotations

from decimal import Decimal

from ntnbinance.features.models import FeatureCandle, FeatureInput

STEP_15M = 900_000
DECISION_TIME_MS = 30 * STEP_15M + 1


def candle(
    index: int,
    *,
    dataset: str = "trade_klines",
    interval: str = "15m",
    close: Decimal | None = None,
    symbol: str = "BTCUSDT",
    event_time_ms: int | None = None,
) -> FeatureCandle:
    step = STEP_15M if interval == "15m" else 4 * STEP_15M
    timestamp = (index + 1) * step
    price = close if close is not None else Decimal(100 + index)
    return FeatureCandle(
        dataset=dataset,
        symbol=symbol,
        interval=interval,
        close_time_ms=timestamp,
        event_time_ms=timestamp if event_time_ms is None else event_time_ms,
        open=price - Decimal("0.4"),
        high=price + Decimal("1.0"),
        low=price - Decimal("1.0"),
        close=price,
        volume_base=Decimal(100 + index),
        trade_count=1000 + index * 10,
        taker_buy_volume_base=Decimal(50 + index) / Decimal(1),
    )


def feature_input(*, symbol: str = "BTCUSDT") -> FeatureInput:
    trade = tuple(candle(index, symbol=symbol) for index in range(30))
    hourly = tuple(candle(index, interval="1h", symbol=symbol) for index in range(7))
    latest_time = trade[-1].close_time_ms
    mark = (
        candle(
            29,
            dataset="mark_price_klines",
            close=trade[-1].close + Decimal("0.10"),
            symbol=symbol,
        ),
    )
    index = (
        candle(
            29,
            dataset="index_price_klines",
            close=trade[-1].close - Decimal("0.10"),
            symbol=symbol,
        ),
    )
    assert latest_time < DECISION_TIME_MS
    return FeatureInput(symbol, DECISION_TIME_MS, trade, hourly, mark, index)
