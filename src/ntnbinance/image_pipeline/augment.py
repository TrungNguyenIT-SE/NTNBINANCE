"""Semantics-preserving image augmentation restricted to TRAIN derivatives."""

from __future__ import annotations

import io
import random

from PIL import Image, ImageEnhance


def augment_for_training(image: Image.Image, *, partition: str, seed: int) -> Image.Image:
    if partition != "TRAIN":
        raise PermissionError("image augmentation is restricted to TRAIN")
    generator = random.Random(seed)
    brightness = generator.uniform(0.92, 1.08)
    contrast = generator.uniform(0.92, 1.08)
    color = generator.uniform(0.95, 1.05)
    quality = generator.randint(88, 96)
    result = ImageEnhance.Brightness(image.convert("RGB")).enhance(brightness)
    result = ImageEnhance.Contrast(result).enhance(contrast)
    result = ImageEnhance.Color(result).enhance(color)
    encoded = io.BytesIO()
    result.save(encoded, format="JPEG", quality=quality, optimize=True)
    encoded.seek(0)
    with Image.open(encoded) as decoded:
        return decoded.convert("RGB")
