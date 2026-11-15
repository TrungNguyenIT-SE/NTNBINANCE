from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from PIL import Image, ImageFilter

from ntnbinance.image_pipeline.models import Candle, ImageDecision
from ntnbinance.image_pipeline.ocr import extract_fields, read_chart_text, verify_ocr_assets
from ntnbinance.image_pipeline.quality import crop_chart, letterbox, measure_quality
from ntnbinance.image_pipeline.renderer import render_chart

from .conftest import DECISION_TIME_MS


@pytest.mark.parametrize("theme", ["DARK", "LIGHT", "ALT"])
@pytest.mark.parametrize("size", [(960, 640), (1280, 720), (1920, 1080)])
def test_quality_and_ocr_pass_supported_matrix(
    candles: tuple[Candle, ...], theme: str, size: tuple[int, int]
) -> None:
    image = render_chart(
        candles,
        symbol="ETHUSDT",
        timeframe="15m",
        decision_time_ms=DECISION_TIME_MS,
        theme=theme,
        size=size,
    )
    quality = measure_quality(image, timeframe="15m")
    assert quality.decision is ImageDecision.ACCEPT
    ocr = read_chart_text(crop_chart(image, quality.roi))
    assert (ocr.symbol, ocr.timeframe, ocr.timestamp_ms) == (
        "ETHUSDT",
        "15m",
        DECISION_TIME_MS,
    )
    assert ocr.last_price == candles[-1].close
    assert ocr.mean_confidence >= 0.70


def test_quality_rejects_non_chart_and_severe_blur(candles: tuple[Candle, ...]) -> None:
    blank = Image.new("RGB", (1280, 720), "#111722")
    blank_quality = measure_quality(blank, timeframe="15m")
    assert blank_quality.decision is ImageDecision.REJECTED_INPUT
    assert "NOT_CANDLE_CHART" in blank_quality.reason_codes

    chart = render_chart(
        candles,
        symbol="ETHUSDT",
        timeframe="15m",
        decision_time_ms=DECISION_TIME_MS,
    )
    blurred = chart.filter(ImageFilter.GaussianBlur(radius=18))
    blur_quality = measure_quality(blurred, timeframe="15m")
    assert blur_quality.decision is ImageDecision.REJECTED_INPUT


def test_letterbox_preserves_content_aspect_ratio() -> None:
    source = Image.new("RGB", (1000, 500), "white")
    result = letterbox(source, (768, 512))
    assert result.size == (768, 512)
    assert result.getpixel((384, 64)) == (255, 255, 255)
    assert result.getpixel((384, 20)) == (18, 22, 30)


def test_exact_field_parser_does_not_fuzzy_correct() -> None:
    parsed = extract_fields("ETHUSDT 1H UTC 2026-11-16 00:00 LAST 1816.05", 0.94)
    assert parsed.symbol == "ETHUSDT"
    assert parsed.timeframe == "1h"
    assert parsed.last_price == Decimal("1816.05")
    missing = extract_fields("ETXUSDT fifteen minutes LAST nope", 0.99)
    assert missing.symbol is None
    assert missing.timeframe is None
    assert missing.last_price is None


def test_model_manifest_fails_closed_on_checksum_mismatch(tmp_path: Path) -> None:
    (tmp_path / "eng.traineddata").write_bytes(b"tampered")
    (tmp_path / "MANIFEST.json").write_text(
        json.dumps({"files": {"eng.traineddata": {"sha256": "00"}}}), encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="checksum mismatch"):
        verify_ocr_assets(tmp_path)


def test_model_manifest_missing_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="missing or invalid"):
        verify_ocr_assets(tmp_path)
