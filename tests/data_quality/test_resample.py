from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from ntnbinance.data_quality.models import CandleRecord
from ntnbinance.data_quality.resample import resample_candles, utc_iso

from .helpers import candle


def test_resample_fifteen_minutes_matches_hand_calculation() -> None:
    records = [
        candle(
            minute,
            open_value=str(100 + minute),
            high=str(102 + minute),
            low=str(99 + minute),
            close=str(101 + minute),
            volume="2",
        )
        for minute in range(15)
    ]
    output, excluded = resample_candles(records, target_interval="15m")
    assert excluded == 0
    assert len(output) == 1
    result = output[0]
    assert (result.open, result.high, result.low, result.close) == (
        Decimal("100"),
        Decimal("116"),
        Decimal("99"),
        Decimal("115"),
    )
    assert result.volume_base == Decimal("30")
    assert result.trade_count == 30
    assert result.source == "DERIVED"


def test_resample_one_hour_from_five_minutes() -> None:
    records = [candle(minute, interval="5m", volume=None) for minute in range(0, 60, 5)]
    output, excluded = resample_candles(records, target_interval="1h")
    assert excluded == 0
    assert len(output) == 1
    assert output[0].volume_base is None
    assert output[0].trade_count is None


@pytest.mark.parametrize(
    "records",
    [
        [candle(minute) for minute in range(14)],
        [candle(minute) for minute in range(15) if minute != 7],
        [replace(candle(minute), is_closed=False) for minute in range(15)],
        [*[candle(minute) for minute in range(15)], candle(0, interval="5m")],
    ],
)
def test_incomplete_gap_open_or_mixed_base_bucket_is_excluded(
    records: list[CandleRecord],
) -> None:
    output, excluded = resample_candles(records, target_interval="15m")
    assert output == []
    assert excluded == 1 or all(not item.is_closed for item in records)


def test_unsupported_target_fails_explicitly() -> None:
    with pytest.raises(KeyError):
        resample_candles([], target_interval="unsupported")


def test_utc_iso_is_explicit() -> None:
    assert utc_iso(0) == "1970-01-01T00:00:00Z"
