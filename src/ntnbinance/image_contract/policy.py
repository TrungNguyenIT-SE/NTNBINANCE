"""Fail-safe metadata and cross-image policy for image-input specification v1."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

OCR_CONFLICT_THRESHOLD = Decimal("0.90")
LAST_PRICE_WARNING_RELATIVE = Decimal("0.0015")
LAST_PRICE_REJECT_RELATIVE = Decimal("0.0035")
MAX_PAIR_CAPTURE_DELTA_MS = 120_000
MAX_LIVE_AGE_MS = 120_000
MAX_FUTURE_CLOCK_SKEW_MS = 30_000


class GateDecision(StrEnum):
    ACCEPT = "ACCEPT"
    REJECTED_INPUT = "REJECTED_INPUT"
    NO_TRADE = "NO_TRADE"


@dataclass(frozen=True, slots=True)
class ImageEvidence:
    assigned_timeframe: str
    declared_symbol: str
    capture_time_ms: int
    quality_passed: bool = True
    ocr_symbol: str | None = None
    ocr_symbol_confidence: Decimal | None = None
    ocr_timeframe: str | None = None
    ocr_timeframe_confidence: Decimal | None = None
    visible_last_price: Decimal | None = None
    authoritative_price: Decimal | None = None


@dataclass(frozen=True, slots=True)
class PairGateResult:
    decision: GateDecision
    reason_codes: tuple[str, ...]


def _conflicts(value: str | None, confidence: Decimal | None, expected: str) -> bool:
    return (
        value is not None
        and confidence is not None
        and confidence >= OCR_CONFLICT_THRESHOLD
        and value.upper() != expected.upper()
    )


def _price_deviation(item: ImageEvidence) -> Decimal | None:
    if item.visible_last_price is None or item.authoritative_price is None:
        return None
    if item.authoritative_price <= 0:
        raise ValueError("authoritative price must be positive")
    return abs(item.visible_last_price - item.authoritative_price) / item.authoritative_price


def evaluate_pair(
    image_1h: ImageEvidence,
    image_15m: ImageEvidence,
    *,
    decision_time_ms: int,
) -> PairGateResult:
    """Evaluate only locked K metadata rules; pixel/OCR extraction belongs to Stage M."""

    images = (image_1h, image_15m)
    if image_1h.assigned_timeframe.lower() != "1h" or image_15m.assigned_timeframe.lower() != "15m":
        return PairGateResult(GateDecision.REJECTED_INPUT, ("ASSIGNED_TIMEFRAME_INVALID",))
    if any(item.declared_symbol not in {"BTCUSDT", "ETHUSDT"} for item in images):
        return PairGateResult(GateDecision.REJECTED_INPUT, ("SYMBOL_OUT_OF_SCOPE",))
    if image_1h.declared_symbol != image_15m.declared_symbol:
        return PairGateResult(GateDecision.REJECTED_INPUT, ("PAIR_SYMBOL_MISMATCH",))
    if not all(item.quality_passed for item in images):
        return PairGateResult(GateDecision.REJECTED_INPUT, ("IMAGE_QUALITY_FAILED",))
    for item in images:
        if _conflicts(item.ocr_symbol, item.ocr_symbol_confidence, item.declared_symbol):
            return PairGateResult(GateDecision.REJECTED_INPUT, ("OCR_SYMBOL_MISMATCH",))
        if _conflicts(item.ocr_timeframe, item.ocr_timeframe_confidence, item.assigned_timeframe):
            return PairGateResult(GateDecision.REJECTED_INPUT, ("OCR_TIMEFRAME_MISMATCH",))
    if any(item.capture_time_ms > decision_time_ms + MAX_FUTURE_CLOCK_SKEW_MS for item in images):
        return PairGateResult(GateDecision.REJECTED_INPUT, ("CAPTURE_TIME_IN_FUTURE",))
    if abs(image_1h.capture_time_ms - image_15m.capture_time_ms) > MAX_PAIR_CAPTURE_DELTA_MS:
        return PairGateResult(GateDecision.NO_TRADE, ("PAIR_CAPTURE_TIME_MISMATCH",))
    if any(decision_time_ms - item.capture_time_ms > MAX_LIVE_AGE_MS for item in images):
        return PairGateResult(GateDecision.NO_TRADE, ("STALE_IMAGE",))
    deviations = [value for item in images if (value := _price_deviation(item)) is not None]
    if any(value > LAST_PRICE_REJECT_RELATIVE for value in deviations):
        return PairGateResult(GateDecision.NO_TRADE, ("LAST_PRICE_MISMATCH",))
    warnings = (
        ("LAST_PRICE_WARNING",)
        if any(value > LAST_PRICE_WARNING_RELATIVE for value in deviations)
        else ()
    )
    return PairGateResult(GateDecision.ACCEPT, warnings)
