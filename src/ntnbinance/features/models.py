"""Typed feature inputs, outputs and coverage decisions."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class FeatureCandle:
    dataset: str
    symbol: str
    interval: str
    close_time_ms: int
    event_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume_base: Decimal | None = None
    trade_count: int | None = None
    taker_buy_volume_base: Decimal | None = None
    is_closed: bool = True


@dataclass(frozen=True, slots=True)
class FeatureInput:
    symbol: str
    decision_time_ms: int
    trade_15m: tuple[FeatureCandle, ...]
    trade_1h: tuple[FeatureCandle, ...]
    mark_15m: tuple[FeatureCandle, ...]
    index_15m: tuple[FeatureCandle, ...]


@dataclass(frozen=True, slots=True)
class FeatureVector:
    version: str
    symbol: str
    decision_time_ms: int
    names: tuple[str, ...]
    values: tuple[float, ...]
    max_event_time_ms: int
    lineage: tuple[tuple[str, int], ...]

    def as_dict(self) -> dict[str, float]:
        return dict(zip(self.names, self.values, strict=True))


@dataclass(frozen=True, slots=True)
class CoverageEvidence:
    dataset: str
    actual: int
    expected: int
    span_days: int

    @property
    def percentage(self) -> float:
        return 0.0 if self.expected <= 0 else self.actual / self.expected * 100


class CoverageDecision(StrEnum):
    INCLUDE = "INCLUDE"
    EXCLUDE = "EXCLUDE"


@dataclass(frozen=True, slots=True)
class CoverageGateResult:
    dataset: str
    decision: CoverageDecision
    percentage: float
    span_days: int
    reason_codes: tuple[str, ...]
