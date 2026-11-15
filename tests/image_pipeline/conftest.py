from __future__ import annotations

from decimal import Decimal

import pytest

from ntnbinance.image_pipeline.models import Candle

DECISION_TIME_MS = 1_794_787_200_000


@pytest.fixture
def candles() -> tuple[Candle, ...]:
    result: list[Candle] = []
    for index in range(96):
        base = Decimal(1800 + (index % 13))
        result.append(
            Candle(
                open_time_ms=DECISION_TIME_MS - (96 - index) * 900_000,
                close_time_ms=DECISION_TIME_MS - (95 - index) * 900_000,
                open=base,
                high=base + Decimal("12"),
                low=base - Decimal("8"),
                close=base + Decimal(5 if index % 3 else -4),
                volume=Decimal(1000 + index * 7),
            )
        )
    return tuple(result)
