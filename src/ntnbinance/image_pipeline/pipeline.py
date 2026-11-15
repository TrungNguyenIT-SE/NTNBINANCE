"""End-to-end fail-safe chart-image analysis and pair cross-checking."""

from __future__ import annotations

from decimal import Decimal

from PIL import Image

from ntnbinance.image_contract.policy import ImageEvidence, evaluate_pair
from ntnbinance.image_pipeline.models import (
    ImageAnalysis,
    ImageDecision,
    PairAnalysis,
)
from ntnbinance.image_pipeline.ocr import read_chart_text
from ntnbinance.image_pipeline.quality import crop_chart, measure_quality

MIN_OCR_CONFIDENCE = 0.70
MAX_OCR_CAPTURE_DELTA_MS = 120_000
TRUSTED_SOURCE_LAYOUTS = {"BINANCE", "TRADINGVIEW", "SYNTHETIC"}


def analyze_image(image: Image.Image, *, timeframe: str) -> ImageAnalysis:
    quality = measure_quality(image, timeframe=timeframe)
    if quality.decision is not ImageDecision.ACCEPT:
        return ImageAnalysis(
            decision=ImageDecision.REJECTED_INPUT,
            reason_codes=quality.reason_codes,
            quality=quality,
            ocr=None,
        )
    ocr = read_chart_text(crop_chart(image, quality.roi))
    required = (ocr.symbol, ocr.timeframe, ocr.timestamp_ms, ocr.last_price)
    if ocr.mean_confidence < MIN_OCR_CONFIDENCE or any(value is None for value in required):
        return ImageAnalysis(
            decision=ImageDecision.NO_TRADE,
            reason_codes=("OCR_EVIDENCE_INSUFFICIENT",),
            quality=quality,
            ocr=ocr,
        )
    return ImageAnalysis(ImageDecision.ACCEPT, (), quality, ocr)


def analyze_pair(
    image_1h: Image.Image,
    image_15m: Image.Image,
    *,
    declared_symbol: str,
    capture_time_1h_ms: int,
    capture_time_15m_ms: int,
    decision_time_ms: int,
    authoritative_price: Decimal,
    source_layout: str,
) -> PairAnalysis:
    analysis_1h = analyze_image(image_1h, timeframe="1h")
    analysis_15m = analyze_image(image_15m, timeframe="15m")
    analyses = (analysis_1h, analysis_15m)
    if any(item.decision is ImageDecision.REJECTED_INPUT for item in analyses):
        reasons = tuple(dict.fromkeys(reason for item in analyses for reason in item.reason_codes))
        return PairAnalysis(ImageDecision.REJECTED_INPUT, reasons, analysis_1h, analysis_15m)
    if source_layout.upper() not in TRUSTED_SOURCE_LAYOUTS:
        return PairAnalysis(
            ImageDecision.NO_TRADE, ("SOURCE_LAYOUT_OOD",), analysis_1h, analysis_15m
        )
    if any(item.decision is ImageDecision.NO_TRADE for item in analyses):
        return PairAnalysis(
            ImageDecision.NO_TRADE,
            ("OCR_EVIDENCE_INSUFFICIENT",),
            analysis_1h,
            analysis_15m,
        )

    ocr_1h, ocr_15m = analysis_1h.ocr, analysis_15m.ocr
    assert ocr_1h is not None
    assert ocr_15m is not None
    if ocr_1h.symbol != declared_symbol or ocr_15m.symbol != declared_symbol:
        return PairAnalysis(
            ImageDecision.REJECTED_INPUT,
            ("OCR_SYMBOL_MISMATCH",),
            analysis_1h,
            analysis_15m,
        )
    if ocr_1h.timeframe != "1h" or ocr_15m.timeframe != "15m":
        return PairAnalysis(
            ImageDecision.REJECTED_INPUT,
            ("OCR_TIMEFRAME_MISMATCH",),
            analysis_1h,
            analysis_15m,
        )
    ocr_timestamps = (ocr_1h.timestamp_ms, ocr_15m.timestamp_ms)
    declared_timestamps = (capture_time_1h_ms, capture_time_15m_ms)
    if any(
        value is None or abs(value - declared) > MAX_OCR_CAPTURE_DELTA_MS
        for value, declared in zip(ocr_timestamps, declared_timestamps, strict=True)
    ):
        return PairAnalysis(
            ImageDecision.NO_TRADE, ("OCR_TIMESTAMP_MISMATCH",), analysis_1h, analysis_15m
        )

    evidence_1h = ImageEvidence(
        assigned_timeframe="1h",
        declared_symbol=declared_symbol,
        capture_time_ms=capture_time_1h_ms,
        ocr_symbol=ocr_1h.symbol,
        ocr_symbol_confidence=Decimal(str(ocr_1h.symbol_confidence)),
        ocr_timeframe=ocr_1h.timeframe,
        ocr_timeframe_confidence=Decimal(str(ocr_1h.timeframe_confidence)),
        visible_last_price=ocr_1h.last_price,
        authoritative_price=authoritative_price,
    )
    evidence_15m = ImageEvidence(
        assigned_timeframe="15m",
        declared_symbol=declared_symbol,
        capture_time_ms=capture_time_15m_ms,
        ocr_symbol=ocr_15m.symbol,
        ocr_symbol_confidence=Decimal(str(ocr_15m.symbol_confidence)),
        ocr_timeframe=ocr_15m.timeframe,
        ocr_timeframe_confidence=Decimal(str(ocr_15m.timeframe_confidence)),
        visible_last_price=ocr_15m.last_price,
        authoritative_price=authoritative_price,
    )
    result = evaluate_pair(evidence_1h, evidence_15m, decision_time_ms=decision_time_ms)
    return PairAnalysis(
        ImageDecision(result.decision.value),
        result.reason_codes,
        analysis_1h,
        analysis_15m,
    )
