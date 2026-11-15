"""Typed contracts for the Stage M image pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ImageDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REJECTED_INPUT = "REJECTED_INPUT"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True, slots=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


@dataclass(frozen=True, slots=True)
class Candle:
    open_time_ms: int
    close_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True, slots=True)
class QualityMetrics:
    roi: Rect
    chart_detected: bool
    blur_score: float
    contrast_score: float
    edge_density: float
    candle_components: int
    right_axis_score: float
    bottom_axis_score: float
    occlusion_fraction: float
    theme: str
    decision: ImageDecision
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OCRResult:
    raw_text: str
    mean_confidence: float
    symbol: str | None
    symbol_confidence: float | None
    timeframe: str | None
    timeframe_confidence: float | None
    timestamp_ms: int | None
    timestamp_confidence: float | None
    last_price: Decimal | None
    last_price_confidence: float | None


@dataclass(frozen=True, slots=True)
class ImageAnalysis:
    decision: ImageDecision
    reason_codes: tuple[str, ...]
    quality: QualityMetrics
    ocr: OCRResult | None


@dataclass(frozen=True, slots=True)
class PairAnalysis:
    decision: ImageDecision
    reason_codes: tuple[str, ...]
    image_1h: ImageAnalysis
    image_15m: ImageAnalysis
