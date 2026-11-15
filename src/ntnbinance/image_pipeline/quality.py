"""Deterministic chart ROI detection and explainable image-quality metrics."""

from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

from ntnbinance.image_pipeline.models import ImageDecision, QualityMetrics, Rect


def _color_mask(array: np.ndarray) -> np.ndarray:
    maximum = array.max(axis=2).astype(np.int16)
    minimum = array.min(axis=2).astype(np.int16)
    return (maximum - minimum >= 45) & (maximum >= 85)


def _expanded_rect(
    bounds: tuple[int, int, int, int], width: int, height: int, *, minimum: tuple[int, int]
) -> Rect:
    left, top, right, bottom = bounds
    margin_x = max(24, int(width * 0.08))
    margin_y = max(24, int(height * 0.16))
    left, right = max(0, left - margin_x), min(width, right + margin_x)
    top, bottom = max(0, top - margin_y), min(height, bottom + margin_y)
    minimum_width, minimum_height = minimum
    if right - left < minimum_width:
        missing = minimum_width - (right - left)
        left = max(0, left - missing // 2)
        right = min(width, left + minimum_width)
        left = max(0, right - minimum_width)
    if bottom - top < minimum_height:
        missing = minimum_height - (bottom - top)
        top = max(0, top - missing // 2)
        bottom = min(height, top + minimum_height)
        top = max(0, bottom - minimum_height)
    return Rect(left, top, right, bottom)


def detect_chart_roi(image: Image.Image) -> tuple[Rect, bool]:
    array = np.asarray(image.convert("RGB"), dtype=np.uint8)
    height, width = array.shape[:2]
    mask = _color_mask(array)
    mask[: int(height * 0.08)] = False
    mask[int(height * 0.88) :] = False
    connected = ndimage.binary_dilation(mask, structure=np.ones((5, 11), dtype=bool))
    labels, count = ndimage.label(connected)
    best: tuple[float, tuple[int, int, int, int]] | None = None
    for label_id in range(1, count + 1):
        ys, xs = np.nonzero(labels == label_id)
        if len(xs) < 25:
            continue
        left, right = int(xs.min()), int(xs.max()) + 1
        top, bottom = int(ys.min()), int(ys.max()) + 1
        component_width, component_height = right - left, bottom - top
        if component_width < width * 0.22 or component_height < height * 0.08:
            continue
        score = component_width * component_height * (len(xs) ** 0.15)
        if best is None or score > best[0]:
            best = (score, (left, top, right, bottom))
    if best is None or best[1][2] - best[1][0] < width * 0.60:
        ys, xs = np.nonzero(mask)
        if len(xs) < 100:
            return Rect(0, 0, width, height), False
        bounds = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
        if bounds[2] - bounds[0] < width * 0.22 or bounds[3] - bounds[1] < height * 0.08:
            return Rect(0, 0, width, height), False
        best = (0.0, bounds)
    return _expanded_rect(best[1], width, height, minimum=(min(720, width), min(480, height))), True


def crop_chart(image: Image.Image, roi: Rect) -> Image.Image:
    return image.crop((roi.left, roi.top, roi.right, roi.bottom))


def letterbox(image: Image.Image, size: tuple[int, int] = (768, 512)) -> Image.Image:
    target_width, target_height = size
    source = image.convert("RGB")
    scale = min(target_width / source.width, target_height / source.height)
    resized = source.resize(
        (max(1, round(source.width * scale)), max(1, round(source.height * scale))),
        Image.Resampling.LANCZOS,
    )
    output = Image.new("RGB", size, (18, 22, 30))
    output.paste(
        resized,
        ((target_width - resized.width) // 2, (target_height - resized.height) // 2),
    )
    return output


def _edge_map(gray: np.ndarray) -> np.ndarray:
    horizontal = ndimage.sobel(gray, axis=1)
    vertical = ndimage.sobel(gray, axis=0)
    return np.asarray(np.hypot(horizontal, vertical))


def _count_candle_components(array: np.ndarray) -> int:
    mask = _color_mask(array)
    mask[int(array.shape[0] * 0.80) :] = False
    labels, count = ndimage.label(mask)
    components = 0
    maximum_width = max(20, int(array.shape[1] * 0.035))
    for label_id in range(1, count + 1):
        ys, xs = np.nonzero(labels == label_id)
        if len(xs) < 4:
            continue
        width = int(xs.max() - xs.min() + 1)
        height = int(ys.max() - ys.min() + 1)
        if 1 <= width <= maximum_width and height >= 4 and height >= width * 0.65:
            components += 1
    return components


def _flat_non_background_fraction(array: np.ndarray) -> float:
    quantized = (array // 8).reshape(-1, 3)
    _, counts = np.unique(quantized, axis=0, return_counts=True)
    if len(counts) < 2:
        return 0.0
    ordered = np.sort(counts)
    return float(ordered[-2] / len(quantized))


def measure_quality(image: Image.Image, *, timeframe: str) -> QualityMetrics:
    roi, detected = detect_chart_roi(image)
    cropped = crop_chart(image, roi)
    array = np.asarray(cropped.convert("RGB"), dtype=np.uint8)
    gray = np.asarray(cropped.convert("L"), dtype=np.float32) / 255.0
    edges = _edge_map(gray)
    blur = float(np.var(ndimage.laplace(gray)) * 10_000)
    contrast = float(np.std(gray))
    edge_density = float(np.mean(edges > 0.18))
    candle_components = _count_candle_components(array)
    right_axis_score = float(np.mean(edges[:, int(edges.shape[1] * 0.86) :] > 0.18))
    bottom_axis_score = float(np.mean(edges[int(edges.shape[0] * 0.86) :, :] > 0.18))
    occlusion = _flat_non_background_fraction(array)
    mean_light = float(np.mean(gray))
    theme = "DARK" if mean_light < 0.48 else "LIGHT"
    reasons: list[str] = []
    if contrast < 0.035:
        reasons.append("THEME_CONTRAST")
    if blur < 1.2:
        reasons.append("BLUR")
    if not detected or candle_components < 12 or edge_density < 0.006:
        reasons.append("NOT_CANDLE_CHART")
    if right_axis_score < 0.004 or bottom_axis_score < 0.002:
        reasons.append("CROP_AXES")
    if occlusion > 0.15:
        reasons.append("OCCLUSION")
    minimum_components = 38 if timeframe == "1h" else 48
    if candle_components < minimum_components:
        reasons.append("TOO_FEW_CANDLES")
    unique = tuple(dict.fromkeys(reasons))
    return QualityMetrics(
        roi=roi,
        chart_detected=detected,
        blur_score=blur,
        contrast_score=contrast,
        edge_density=edge_density,
        candle_components=candle_components,
        right_axis_score=right_axis_score,
        bottom_axis_score=bottom_axis_score,
        occlusion_fraction=occlusion,
        theme=theme,
        decision=ImageDecision.REJECTED_INPUT if unique else ImageDecision.ACCEPT,
        reason_codes=unique,
    )
