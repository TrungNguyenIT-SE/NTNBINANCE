from __future__ import annotations

import hashlib
import json
import struct
import tomllib
from collections import Counter
from pathlib import Path
from typing import cast

from ntnbinance.image_contract import policy

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "images"


def _json(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def _review(path: Path) -> tuple[list[str], dict[str, tuple[str, str]]]:
    raw = _json(path)
    assert raw["blind_to_other_round"] is True
    items = raw["items"]
    assert isinstance(items, list)
    order = [str(item["pair_id"]) for item in items]
    values = {str(item["pair_id"]): (str(item["decision"]), str(item["reason"])) for item in items}
    return order, values


def _cohen_kappa(left: list[str], right: list[str]) -> float:
    labels = sorted(set(left) | set(right))
    observed = sum(a == b for a, b in zip(left, right, strict=True)) / len(left)
    left_counts, right_counts = Counter(left), Counter(right)
    expected = sum(left_counts[label] * right_counts[label] for label in labels) / len(left) ** 2
    return (observed - expected) / (1 - expected)


def test_locked_image_limits_are_explicit_and_bounded() -> None:
    config = tomllib.loads(
        (ROOT / "configs/images/image-input-v1.toml").read_text(encoding="utf-8")
    )
    assert config["allowed_formats"] == ["PNG", "JPEG", "WEBP"]
    assert config["max_file_bytes"] == 10 * 1024 * 1024
    assert (config["min_width_px"], config["min_height_px"]) == (800, 600)
    assert (config["max_width_px"], config["max_height_px"]) == (4096, 4096)
    assert config["max_pixels"] == 4096 * 4096
    assert config["timeframes"]["1h"]["minimum_closed_candles"] == 60
    assert config["timeframes"]["15m"]["minimum_closed_candles"] == 80
    assert config["max_pair_capture_delta_seconds"] * 1000 == policy.MAX_PAIR_CAPTURE_DELTA_MS
    assert config["max_live_age_seconds"] * 1000 == policy.MAX_LIVE_AGE_MS
    assert config["max_future_clock_skew_seconds"] * 1000 == policy.MAX_FUTURE_CLOCK_SKEW_MS
    assert config["ocr_conflict_threshold"] == str(policy.OCR_CONFLICT_THRESHOLD)
    assert config["last_price_warning_relative"] == str(policy.LAST_PRICE_WARNING_RELATIVE)
    assert config["last_price_reject_relative"] == str(policy.LAST_PRICE_REJECT_RELATIVE)


def test_golden_set_files_match_manifest_and_png_contract() -> None:
    manifest = _json(FIXTURES / "manifest.json")
    pairs = manifest["pairs"]
    assert isinstance(pairs, list)
    assert len(pairs) == 12
    assert Counter(str(pair["expected_decision"]) for pair in pairs) == {
        "ACCEPT": 4,
        "REJECTED_INPUT": 6,
        "NO_TRADE": 2,
    }
    assert len({str(pair["primary_reason"]) for pair in pairs}) >= 10
    referenced: set[str] = set()
    for pair in pairs:
        images = pair["images"]
        assert isinstance(images, list)
        assert {str(item["slot"]) for item in images} == {"1h", "15m"}
        for image in images:
            path = FIXTURES / str(image["path"])
            payload = path.read_bytes()
            assert hashlib.sha256(payload).hexdigest() == image["sha256"]
            assert payload.startswith(b"\x89PNG\r\n\x1a\n")
            assert struct.unpack(">II", payload[16:24]) == (960, 640)
            referenced.add(path.name)
    assert len(referenced) == 24
    assert referenced == {path.name for path in FIXTURES.glob("*.png")}


def test_two_blind_review_rounds_meet_agreement_gate() -> None:
    manifest = _json(FIXTURES / "manifest.json")
    pairs = manifest["pairs"]
    assert isinstance(pairs, list)
    expected = {
        str(pair["pair_id"]): (str(pair["expected_decision"]), str(pair["primary_reason"]))
        for pair in pairs
    }
    order_a, review_a = _review(ROOT / "reports/image-review-round-a.json")
    order_b, review_b = _review(ROOT / "reports/image-review-round-b.json")
    assert order_a != order_b
    assert review_a == expected == review_b
    ids = sorted(expected)
    verdict_a = [review_a[item][0] for item in ids]
    verdict_b = [review_b[item][0] for item in ids]
    agreement = sum(a == b for a, b in zip(verdict_a, verdict_b, strict=True)) / len(ids)
    assert agreement >= 0.90
    assert _cohen_kappa(verdict_a, verdict_b) >= 0.80
