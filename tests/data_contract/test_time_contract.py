from datetime import UTC, datetime, timedelta, timezone

import pytest

from ntnbinance.data_contract import (
    SCHEMA_VERSION,
    CandleIdentity,
    CandleObservation,
    DataContractError,
    MarketType,
    PriceKind,
    assert_candles_usable,
    expected_close_time,
    require_utc,
)

OPEN = datetime(2026, 11, 9, 12, 0, tzinfo=UTC)
CLOSE = datetime(2026, 11, 9, 12, 14, 59, 999000, tzinfo=UTC)
BOUNDARY = datetime(2026, 11, 9, 12, 15, tzinfo=UTC)


def make_candle(
    *,
    is_closed: bool = True,
    event_time: datetime = CLOSE,
    ingested_at: datetime = BOUNDARY,
    close_time: datetime = CLOSE,
    schema_version: str = SCHEMA_VERSION,
) -> CandleObservation:
    identity = CandleIdentity(
        venue="BINANCE",
        market=MarketType.USD_M_PERPETUAL,
        instrument="BTCUSDT",
        interval="15m",
        price_kind=PriceKind.TRADE,
        open_time=OPEN,
    )
    return CandleObservation(
        identity=identity,
        close_time=close_time,
        event_time=event_time,
        ingested_at=ingested_at,
        is_closed=is_closed,
        schema_version=schema_version,
    )


def test_expected_close_time_uses_inclusive_final_millisecond() -> None:
    assert expected_close_time(OPEN, "15m") == CLOSE


def test_closed_candle_is_usable_at_next_interval_boundary() -> None:
    candle = make_candle()
    assert candle.available_at == BOUNDARY
    assert candle.is_usable_at(BOUNDARY)
    candle.require_usable_at(BOUNDARY)
    assert_candles_usable([candle], BOUNDARY)


def test_open_candle_is_never_usable_even_after_close_time() -> None:
    candle = make_candle(is_closed=False)
    assert not candle.is_usable_at(BOUNDARY + timedelta(minutes=1))
    with pytest.raises(DataContractError, match="is_closed must be true"):
        candle.require_usable_at(BOUNDARY + timedelta(minutes=1))


@pytest.mark.parametrize(
    ("event_time", "ingested_at", "decision_time"),
    [
        (CLOSE, BOUNDARY + timedelta(seconds=2), BOUNDARY),
        (BOUNDARY + timedelta(seconds=2), BOUNDARY + timedelta(seconds=3), BOUNDARY),
    ],
)
def test_future_or_late_observation_is_rejected(
    event_time: datetime, ingested_at: datetime, decision_time: datetime
) -> None:
    candle = make_candle(event_time=event_time, ingested_at=ingested_at)
    assert not candle.is_usable_at(decision_time)
    with pytest.raises(DataContractError, match="not available at decision_time"):
        assert_candles_usable([candle], decision_time)


def test_decision_before_exclusive_boundary_is_rejected() -> None:
    assert not make_candle(ingested_at=CLOSE).is_usable_at(CLOSE)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (datetime(2026, 11, 9, 12, 0), "timezone-aware UTC"),  # noqa: DTZ001
        (
            datetime(2026, 11, 9, 19, 0, tzinfo=timezone(timedelta(hours=7))),
            "UTC offset",
        ),
    ],
)
def test_timestamp_must_be_explicit_utc(value: datetime, message: str) -> None:
    with pytest.raises(DataContractError, match=message):
        require_utc(value, "sample_time")


def test_zero_offset_timestamp_is_normalized_to_utc() -> None:
    value = datetime(2026, 11, 9, 12, 0, tzinfo=timezone(timedelta(0), "ZERO"))
    assert require_utc(value, "sample_time").tzinfo is UTC


def test_invalid_interval_is_rejected() -> None:
    with pytest.raises(DataContractError, match="unsupported fixed interval"):
        expected_close_time(OPEN, "1M")


def test_wrong_close_time_is_rejected() -> None:
    with pytest.raises(DataContractError, match="close_time must equal"):
        make_candle(close_time=BOUNDARY)


def test_event_cannot_precede_open() -> None:
    with pytest.raises(DataContractError, match="event_time cannot precede"):
        make_candle(event_time=OPEN - timedelta(milliseconds=1))


def test_ingestion_cannot_precede_event() -> None:
    with pytest.raises(DataContractError, match="ingested_at cannot precede"):
        make_candle(event_time=BOUNDARY, ingested_at=CLOSE)


def test_unknown_schema_version_is_rejected() -> None:
    with pytest.raises(DataContractError, match="unsupported schema_version"):
        make_candle(schema_version="2.0.0")
