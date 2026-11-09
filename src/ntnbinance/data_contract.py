"""Executable time and identity contract for market-data records."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Final

SCHEMA_VERSION: Final = "1.0.0"
MILLISECOND: Final = timedelta(milliseconds=1)
INTERVAL_DURATION: Final[dict[str, timedelta]] = {
    "1m": timedelta(minutes=1),
    "3m": timedelta(minutes=3),
    "5m": timedelta(minutes=5),
    "15m": timedelta(minutes=15),
    "30m": timedelta(minutes=30),
    "1h": timedelta(hours=1),
    "2h": timedelta(hours=2),
    "4h": timedelta(hours=4),
    "6h": timedelta(hours=6),
    "8h": timedelta(hours=8),
    "12h": timedelta(hours=12),
    "1d": timedelta(days=1),
}


class DataContractError(ValueError):
    """A record is ambiguous or could introduce look-ahead leakage."""


class MarketType(StrEnum):
    """Markets admitted by schema v1."""

    USD_M_PERPETUAL = "USD_M_PERPETUAL"


class PriceKind(StrEnum):
    """Candle sources that must remain separate in storage."""

    TRADE = "TRADE"
    MARK = "MARK"
    INDEX = "INDEX"


class QualityFlag(StrEnum):
    """Stable, non-destructive data-quality annotations."""

    DUPLICATE_KEY = "DUPLICATE_KEY"
    MISSING_BAR_BEFORE = "MISSING_BAR_BEFORE"
    OUT_OF_ORDER = "OUT_OF_ORDER"
    CLOCK_SKEW = "CLOCK_SKEW"
    INVALID_OHLC = "INVALID_OHLC"
    NEGATIVE_VOLUME = "NEGATIVE_VOLUME"
    INCOMPLETE_BAR = "INCOMPLETE_BAR"
    SOURCE_CONFLICT = "SOURCE_CONFLICT"
    LATE_ARRIVAL = "LATE_ARRIVAL"
    NULL_REQUIRED_FIELD = "NULL_REQUIRED_FIELD"
    UNKNOWN_SCHEMA = "UNKNOWN_SCHEMA"


def require_utc(value: datetime, field_name: str) -> datetime:
    """Require an aware, zero-offset timestamp and normalize to ``UTC``."""

    if value.tzinfo is None or value.utcoffset() is None:
        raise DataContractError(f"{field_name} must be timezone-aware UTC")
    if value.utcoffset() != timedelta(0):
        raise DataContractError(f"{field_name} must have UTC offset +00:00")
    return value.astimezone(UTC)


def expected_close_time(open_time: datetime, interval: str) -> datetime:
    """Return Binance's inclusive final millisecond for a fixed interval."""

    normalized_open = require_utc(open_time, "open_time")
    try:
        duration = INTERVAL_DURATION[interval]
    except KeyError as error:
        raise DataContractError(f"unsupported fixed interval: {interval}") from error
    return normalized_open + duration - MILLISECOND


@dataclass(frozen=True, slots=True)
class CandleIdentity:
    """Stable primary key for one clean-layer candle."""

    venue: str
    market: MarketType
    instrument: str
    interval: str
    price_kind: PriceKind
    open_time: datetime

    def __post_init__(self) -> None:
        if self.venue != "BINANCE":
            raise DataContractError("venue must be BINANCE in schema v1")
        if not self.instrument or self.instrument != self.instrument.upper():
            raise DataContractError("instrument must be a non-empty uppercase symbol/pair")
        if self.interval not in INTERVAL_DURATION:
            raise DataContractError(f"unsupported fixed interval: {self.interval}")
        object.__setattr__(self, "open_time", require_utc(self.open_time, "open_time"))

    @property
    def unique_key(self) -> tuple[str, str, str, str, str, datetime]:
        return (
            self.venue,
            self.market.value,
            self.instrument,
            self.interval,
            self.price_kind.value,
            self.open_time,
        )


@dataclass(frozen=True, slots=True)
class CandleObservation:
    """Timing envelope required before a candle may enter a prediction."""

    identity: CandleIdentity
    close_time: datetime
    event_time: datetime
    ingested_at: datetime
    is_closed: bool
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in ("close_time", "event_time", "ingested_at"):
            object.__setattr__(self, name, require_utc(getattr(self, name), name))
        expected = expected_close_time(self.identity.open_time, self.identity.interval)
        if self.close_time != expected:
            raise DataContractError(
                f"close_time must equal open_time + interval - 1 ms ({expected.isoformat()})"
            )
        if self.event_time < self.identity.open_time:
            raise DataContractError("event_time cannot precede open_time")
        if self.ingested_at < self.event_time:
            raise DataContractError("ingested_at cannot precede event_time")
        if self.schema_version != SCHEMA_VERSION:
            raise DataContractError(f"unsupported schema_version: {self.schema_version}")

    @property
    def available_at(self) -> datetime:
        """First instant at which all time constraints are satisfied."""

        return max(self.close_time + MILLISECOND, self.event_time, self.ingested_at)

    def is_usable_at(self, decision_time: datetime) -> bool:
        normalized_decision = require_utc(decision_time, "decision_time")
        return self.is_closed and self.available_at <= normalized_decision

    def require_usable_at(self, decision_time: datetime) -> None:
        if not self.is_closed:
            raise DataContractError("candle is not final: is_closed must be true")
        normalized_decision = require_utc(decision_time, "decision_time")
        if self.available_at > normalized_decision:
            raise DataContractError(
                "candle was not available at decision_time: "
                f"available_at={self.available_at.isoformat()}"
            )


def assert_unique_candles(candles: Iterable[CandleObservation]) -> None:
    """Reject duplicate clean-layer candle identities."""

    seen: set[tuple[str, str, str, str, str, datetime]] = set()
    for candle in candles:
        key = candle.identity.unique_key
        if key in seen:
            raise DataContractError(f"duplicate candle unique_key: {key}")
        seen.add(key)


def assert_candles_usable(candles: Iterable[CandleObservation], decision_time: datetime) -> None:
    """Apply the no-look-ahead gate to prediction inputs."""

    normalized_decision = require_utc(decision_time, "decision_time")
    for candle in candles:
        candle.require_usable_at(normalized_decision)
