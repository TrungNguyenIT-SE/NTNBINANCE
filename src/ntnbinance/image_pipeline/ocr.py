"""Pinned, local-only Tesseract OCR with conservative field extraction."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageOps
from tesserocr import PSM, PyTessBaseAPI

from ntnbinance.image_pipeline.models import OCRResult

MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / "ocr"
_SYMBOL_PATTERN = re.compile(r"\b(BTC\s*USDT|ETH\s*USDT)\b", re.IGNORECASE)
_TIMEFRAME_PATTERN = re.compile(r"(?:^|\s)(1\s*H|15\s*M)(?:\s|$)", re.IGNORECASE)
_TIMESTAMP_PATTERN = re.compile(
    r"(?:UTC\s*)?(20\d{2})[-/.](\d{2})[-/.](\d{2})\s+(\d{2}):(\d{2})",
    re.IGNORECASE,
)
_PRICE_PATTERN = re.compile(r"\bLAST\s+([0-9][0-9,.]*[0-9])\b", re.IGNORECASE)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verify_ocr_assets(model_dir: Path = MODEL_DIR) -> None:
    """Fail closed if the committed model differs from its pinned manifest."""

    manifest_path = model_dir / "MANIFEST.json"
    try:
        manifest: dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries: dict[str, dict[str, str]] = manifest["files"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError("OCR model manifest is missing or invalid") from exc
    for name, metadata in entries.items():
        path = model_dir / name
        if not path.is_file() or _sha256(path) != metadata["sha256"].upper():
            raise RuntimeError(f"OCR asset checksum mismatch: {name}")


def _prepare(image: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(image)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.35)
    if gray.width < 1200:
        scale = 1200 / gray.width
        gray = gray.resize((1200, round(gray.height * scale)), Image.Resampling.LANCZOS)
    return gray


def _confidence(confidences: list[int]) -> float:
    valid = [value for value in confidences if value >= 0]
    return sum(valid) / len(valid) / 100 if valid else 0.0


def _parse_price(value: str) -> Decimal | None:
    compact = value.replace(",", "")
    try:
        parsed = Decimal(compact)
    except InvalidOperation:
        return None
    return parsed if parsed > 0 else None


def extract_fields(raw_text: str, confidence: float) -> OCRResult:
    """Extract only exact, allow-listed fields; do not fuzzy-correct OCR output."""

    flattened = " ".join(raw_text.split())
    symbol_match = _SYMBOL_PATTERN.search(flattened)
    timeframe_match = _TIMEFRAME_PATTERN.search(f" {flattened} ")
    timestamp_match = _TIMESTAMP_PATTERN.search(flattened)
    price_match = _PRICE_PATTERN.search(flattened)
    symbol = symbol_match.group(1).replace(" ", "").upper() if symbol_match else None
    timeframe = timeframe_match.group(1).replace(" ", "").lower() if timeframe_match else None
    timestamp_ms: int | None = None
    if timestamp_match:
        try:
            year, month, day, hour, minute = (int(value) for value in timestamp_match.groups())
            parsed = datetime(year, month, day, hour, minute, tzinfo=UTC)
            timestamp_ms = int(parsed.timestamp() * 1000)
        except ValueError:
            timestamp_ms = None
    price = _parse_price(price_match.group(1)) if price_match else None
    return OCRResult(
        raw_text=raw_text.strip(),
        mean_confidence=confidence,
        symbol=symbol,
        symbol_confidence=confidence if symbol is not None else None,
        timeframe=timeframe,
        timeframe_confidence=confidence if timeframe is not None else None,
        timestamp_ms=timestamp_ms,
        timestamp_confidence=confidence if timestamp_ms is not None else None,
        last_price=price,
        last_price_confidence=confidence if price is not None else None,
    )


def read_chart_text(image: Image.Image, model_dir: Path = MODEL_DIR) -> OCRResult:
    verify_ocr_assets(model_dir)
    # The locked v1 contract requires identity/time evidence in the chart header.
    # Restricting OCR to this band avoids candle/grid strokes becoming fake text.
    header = image.crop((0, 0, image.width, max(1, round(image.height * 0.18))))
    prepared = _prepare(header)
    with PyTessBaseAPI(path=str(model_dir), lang="eng", psm=PSM.SPARSE_TEXT) as api:
        api.SetVariable("user_defined_dpi", "150")
        api.SetImage(prepared)
        raw_text = api.GetUTF8Text()
        confidence = _confidence(api.AllWordConfidences())
    return extract_fields(raw_text, confidence)
