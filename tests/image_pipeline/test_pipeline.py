from __future__ import annotations

from PIL import Image

from ntnbinance.image_pipeline.models import Candle, ImageDecision
from ntnbinance.image_pipeline.pipeline import analyze_image, analyze_pair
from ntnbinance.image_pipeline.renderer import render_chart

from .conftest import DECISION_TIME_MS


def _pair(candles: tuple[Candle, ...]) -> tuple[Image.Image, Image.Image]:
    return (
        render_chart(
            candles,
            symbol="ETHUSDT",
            timeframe="1h",
            decision_time_ms=DECISION_TIME_MS,
        ),
        render_chart(
            candles,
            symbol="ETHUSDT",
            timeframe="15m",
            decision_time_ms=DECISION_TIME_MS,
        ),
    )


def test_pair_accepts_consistent_current_images(candles: tuple[Candle, ...]) -> None:
    image_1h, image_15m = _pair(candles)
    result = analyze_pair(
        image_1h,
        image_15m,
        declared_symbol="ETHUSDT",
        capture_time_1h_ms=DECISION_TIME_MS,
        capture_time_15m_ms=DECISION_TIME_MS,
        decision_time_ms=DECISION_TIME_MS,
        authoritative_price=candles[-1].close,
        source_layout="SYNTHETIC",
    )
    assert result.decision is ImageDecision.ACCEPT


def test_pair_rejects_symbol_mismatch(candles: tuple[Candle, ...]) -> None:
    image_1h, image_15m = _pair(candles)
    result = analyze_pair(
        image_1h,
        image_15m,
        declared_symbol="BTCUSDT",
        capture_time_1h_ms=DECISION_TIME_MS,
        capture_time_15m_ms=DECISION_TIME_MS,
        decision_time_ms=DECISION_TIME_MS,
        authoritative_price=candles[-1].close,
        source_layout="BINANCE",
    )
    assert result.decision is ImageDecision.REJECTED_INPUT
    assert result.reason_codes == ("OCR_SYMBOL_MISMATCH",)


def test_pair_no_trade_for_stale_price_and_ood(candles: tuple[Candle, ...]) -> None:
    image_1h, image_15m = _pair(candles)
    stale = analyze_pair(
        image_1h,
        image_15m,
        declared_symbol="ETHUSDT",
        capture_time_1h_ms=DECISION_TIME_MS,
        capture_time_15m_ms=DECISION_TIME_MS,
        decision_time_ms=DECISION_TIME_MS + 180_001,
        authoritative_price=candles[-1].close,
        source_layout="BINANCE",
    )
    assert stale.decision is ImageDecision.NO_TRADE
    assert stale.reason_codes == ("STALE_IMAGE",)
    ood = analyze_pair(
        image_1h,
        image_15m,
        declared_symbol="ETHUSDT",
        capture_time_1h_ms=DECISION_TIME_MS,
        capture_time_15m_ms=DECISION_TIME_MS,
        decision_time_ms=DECISION_TIME_MS + 180_001,
        authoritative_price=candles[-1].close,
        source_layout="UNKNOWN_SCREEN",
    )
    assert ood.decision is ImageDecision.NO_TRADE
    assert ood.reason_codes == ("SOURCE_LAYOUT_OOD",)


def test_pair_rejects_non_chart_before_ocr(candles: tuple[Candle, ...]) -> None:
    _, image_15m = _pair(candles)
    blank = Image.new("RGB", image_15m.size, "black")
    result = analyze_pair(
        blank,
        image_15m,
        declared_symbol="ETHUSDT",
        capture_time_1h_ms=DECISION_TIME_MS,
        capture_time_15m_ms=DECISION_TIME_MS,
        decision_time_ms=DECISION_TIME_MS,
        authoritative_price=candles[-1].close,
        source_layout="BINANCE",
    )
    assert result.decision is ImageDecision.REJECTED_INPUT


def test_image_returns_no_trade_when_header_evidence_is_missing(
    candles: tuple[Candle, ...],
) -> None:
    image = render_chart(
        candles,
        symbol="ETHUSDT",
        timeframe="15m",
        decision_time_ms=DECISION_TIME_MS,
    )
    image.paste("#0d1421", (0, 0, image.width, round(image.height * 0.13)))
    result = analyze_image(image, timeframe="15m")
    assert result.decision is ImageDecision.NO_TRADE
    assert result.reason_codes == ("OCR_EVIDENCE_INSUFFICIENT",)
