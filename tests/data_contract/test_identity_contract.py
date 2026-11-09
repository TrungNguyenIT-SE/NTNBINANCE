from datetime import UTC, datetime

import pytest

from ntnbinance.data_contract import (
    CandleIdentity,
    CandleObservation,
    DataContractError,
    MarketType,
    PriceKind,
    QualityFlag,
    assert_unique_candles,
)

OPEN = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)
CLOSE = datetime(2026, 11, 9, 12, 14, 59, 999000, tzinfo=UTC)
BOUNDARY = datetime(2026, 11, 9, 12, 15, tzinfo=UTC)


def identity(**overrides: object) -> CandleIdentity:
    values: dict[str, object] = {
        "venue": "BINANCE",
        "market": MarketType.USD_M_PERPETUAL,
        "instrument": "BTCUSDT",
        "interval": "15m",
        "price_kind": PriceKind.TRADE,
        "open_time": OPEN,
    }
    values.update(overrides)
    return CandleIdentity(**values)  # type: ignore[arg-type]


def observation(candle_identity: CandleIdentity) -> CandleObservation:
    return CandleObservation(
        identity=candle_identity,
        close_time=CLOSE,
        event_time=CLOSE,
        ingested_at=BOUNDARY,
        is_closed=True,
    )


def test_unique_key_contains_price_kind_and_open_time() -> None:
    assert identity().unique_key == (
        "BINANCE",
        "USD_M_PERPETUAL",
        "BTCUSDT",
        "15m",
        "TRADE",
        OPEN,
    )


def test_different_price_kinds_do_not_collide() -> None:
    trade = observation(identity(price_kind=PriceKind.TRADE))
    mark = observation(identity(price_kind=PriceKind.MARK))
    assert_unique_candles([trade, mark])


def test_duplicate_candle_is_rejected() -> None:
    candle = observation(identity())
    with pytest.raises(DataContractError, match="duplicate candle unique_key"):
        assert_unique_candles([candle, candle])


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"venue": "OTHER"}, "venue must be BINANCE"),
        ({"instrument": "btcusdt"}, "uppercase"),
        ({"instrument": ""}, "non-empty"),
        ({"interval": "7m"}, "unsupported fixed interval"),
    ],
)
def test_invalid_identity_is_rejected(overrides: dict[str, object], message: str) -> None:
    with pytest.raises(DataContractError, match=message):
        identity(**overrides)


def test_quality_flags_are_stable_machine_values() -> None:
    assert QualityFlag.INCOMPLETE_BAR.value == "INCOMPLETE_BAR"
    assert QualityFlag.LATE_ARRIVAL.value == "LATE_ARRIVAL"
