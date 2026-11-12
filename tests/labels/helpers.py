from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from ntnbinance.data_quality.models import CandleRecord
from ntnbinance.labels.models import LabelConfig

CONFIG_PATH = Path("configs/labels/triple-barrier-v1.toml")


def candle(
    minute: int,
    *,
    interval: str,
    open_value: str,
    high: str,
    low: str,
    close: str,
    identity: str,
) -> CandleRecord:
    step_ms = {"1m": 60_000, "15m": 900_000}[interval]
    open_time = minute * 60_000
    close_time = open_time + step_ms - 1
    return CandleRecord(
        dataset="trade_klines",
        symbol="BTCUSDT",
        interval=interval,
        open_time_ms=open_time,
        close_time_ms=close_time,
        event_time_ms=close_time,
        ingested_at=datetime(1970, 1, 1, tzinfo=UTC) + timedelta(milliseconds=close_time + 1),
        open=Decimal(open_value),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume_base=Decimal("1"),
        volume_quote=Decimal("100"),
        trade_count=1,
        taker_buy_volume_base=Decimal("0.5"),
        taker_buy_volume_quote=Decimal("50"),
        is_closed=True,
        source="DERIVED" if interval == "15m" else "REST",
        raw_identity=identity,
        raw_ref=f"raw:{identity}",
    )


def config() -> LabelConfig:
    return LabelConfig.load(CONFIG_PATH)


def sample_window(
    *, history_high: str = "101", history_low: str = "99"
) -> tuple[list[CandleRecord], list[CandleRecord], list[CandleRecord]]:
    neutral_high = history_high
    neutral_low = history_low
    history = [
        candle(
            minute,
            interval="15m",
            open_value="100",
            high=history_high,
            low=history_low,
            close="100",
            identity=f"history-{minute}",
        )
        for minute in range(0, 225, 15)
    ]
    future = [
        candle(
            minute,
            interval="15m",
            open_value="100",
            high=neutral_high,
            low=neutral_low,
            close="100",
            identity=f"future-{minute}",
        )
        for minute in range(225, 285, 15)
    ]
    intrabars = [
        candle(
            minute,
            interval="1m",
            open_value="100",
            high=neutral_high,
            low=neutral_low,
            close="100",
            identity=f"intra-{minute}",
        )
        for minute in range(225, 285)
    ]
    return history, future, intrabars


def touched(record: CandleRecord, *, high: str = "101", low: str = "99") -> CandleRecord:
    return replace(record, high=Decimal(high), low=Decimal(low))
