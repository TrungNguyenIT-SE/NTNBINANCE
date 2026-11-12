"""Small deterministic candle fixtures for Stage F tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from ntnbinance.data_quality.models import CandleRecord


def candle(
    minute: int = 0,
    *,
    dataset: str = "trade_klines",
    interval: str = "1m",
    open_value: str = "100",
    high: str = "102",
    low: str = "99",
    close: str = "101",
    volume: str | None = "10",
    closed: bool = True,
    source: str = "REST",
    identity: str | None = None,
) -> CandleRecord:
    step_ms = {"1m": 60_000, "5m": 300_000, "15m": 900_000, "1h": 3_600_000}[interval]
    open_time = minute * 60_000
    event_time = open_time + step_ms - 1
    return CandleRecord(
        dataset=dataset,
        symbol="BTCUSDT",
        interval=interval,
        open_time_ms=open_time,
        close_time_ms=event_time,
        event_time_ms=event_time,
        ingested_at=datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=event_time + 1),
        open=Decimal(open_value),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume_base=None if volume is None else Decimal(volume),
        volume_quote=None if volume is None else Decimal(volume) * Decimal("100"),
        trade_count=None if volume is None else 2,
        taker_buy_volume_base=None if volume is None else Decimal(volume) / 2,
        taker_buy_volume_quote=None if volume is None else Decimal(volume) * Decimal("50"),
        is_closed=closed,
        source=source,
        raw_identity=identity or f"id-{dataset}-{interval}-{minute}-{source}",
        raw_ref=f"raw:{minute}",
    )
