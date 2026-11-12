"""Typed records shared by Stage F quality components."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from typing import Final

from ntnbinance.data_contract import QualityFlag

CRITICAL_FLAGS: Final = frozenset(
    {
        QualityFlag.INCOMPLETE_BAR,
        QualityFlag.INVALID_OHLC,
        QualityFlag.NEGATIVE_VOLUME,
        QualityFlag.INVALID_VOLUME,
        QualityFlag.NULL_REQUIRED_FIELD,
        QualityFlag.SOURCE_CONFLICT,
        QualityFlag.UNKNOWN_SCHEMA,
    }
)


@dataclass(frozen=True, slots=True)
class CandleRecord:
    dataset: str
    symbol: str
    interval: str
    open_time_ms: int
    close_time_ms: int
    event_time_ms: int
    ingested_at: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume_base: Decimal | None
    volume_quote: Decimal | None
    trade_count: int | None
    taker_buy_volume_base: Decimal | None
    taker_buy_volume_quote: Decimal | None
    is_closed: bool
    source: str
    raw_identity: str
    raw_ref: str
    quality_flags: frozenset[QualityFlag] = frozenset()

    @property
    def logical_key(self) -> tuple[str, str, str, int]:
        return (self.dataset, self.symbol, self.interval, self.open_time_ms)

    @property
    def core_values(self) -> tuple[object, ...]:
        return (
            self.close_time_ms,
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume_base,
            self.volume_quote,
            self.trade_count,
            self.taker_buy_volume_base,
            self.taker_buy_volume_quote,
        )

    @property
    def has_critical_flag(self) -> bool:
        return bool(self.quality_flags & CRITICAL_FLAGS)

    def add_flags(self, *flags: QualityFlag) -> CandleRecord:
        return replace(self, quality_flags=self.quality_flags.union(flags))


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    dataset: str
    symbol: str
    interval: str
    open_time_ms: int | None
    raw_identity: str
    raw_ref: str
    quality_flags: tuple[str, ...]
    reason: str
    payload_json: str


@dataclass(frozen=True, slots=True)
class CoverageRecord:
    dataset: str
    symbol: str
    interval: str
    date_utc: str
    expected: int
    actual: int
    missing: int
    coverage_percent: float


@dataclass(frozen=True, slots=True)
class FeatureCoverageRecord:
    dataset: str
    symbol: str
    cadence: str
    date_utc: str
    expected: int
    actual: int
    missing: int
    coverage_percent: float


@dataclass(frozen=True, slots=True)
class QualityStats:
    raw_records: int
    parsed_candles: int
    clean_base_candles: int
    resampled_candles: int
    quarantine_records: int
    duplicate_observations: int
    source_conflicts: int
    missing_bars: int
    out_of_order_observations: int
    clock_skew_observations: int
