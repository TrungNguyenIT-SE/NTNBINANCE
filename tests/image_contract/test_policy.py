from dataclasses import replace
from decimal import Decimal

import pytest

from ntnbinance.image_contract import GateDecision, ImageEvidence, evaluate_pair

NOW = 1_800_000_000_000


def evidence(timeframe: str) -> ImageEvidence:
    return ImageEvidence(
        assigned_timeframe=timeframe,
        declared_symbol="BTCUSDT",
        capture_time_ms=NOW - 30_000,
        ocr_symbol="BTCUSDT",
        ocr_symbol_confidence=Decimal("0.95"),
        ocr_timeframe=timeframe,
        ocr_timeframe_confidence=Decimal("0.95"),
        visible_last_price=Decimal("100"),
        authoritative_price=Decimal("100"),
    )


def decision(
    one_hour: ImageEvidence, fifteen_minute: ImageEvidence
) -> tuple[GateDecision, tuple[str, ...]]:
    result = evaluate_pair(one_hour, fifteen_minute, decision_time_ms=NOW)
    return result.decision, result.reason_codes


def test_valid_pair_and_price_warning_are_explicit() -> None:
    one_hour, fifteen = evidence("1h"), evidence("15m")
    assert decision(one_hour, fifteen) == (GateDecision.ACCEPT, ())

    warning = replace(fifteen, visible_last_price=Decimal("100.2"))
    assert decision(one_hour, warning) == (GateDecision.ACCEPT, ("LAST_PRICE_WARNING",))


@pytest.mark.parametrize(
    ("one_hour", "fifteen", "reason"),
    [
        (
            replace(evidence("1h"), assigned_timeframe="15m"),
            evidence("15m"),
            "ASSIGNED_TIMEFRAME_INVALID",
        ),
        (
            replace(evidence("1h"), declared_symbol="SOLUSDT"),
            evidence("15m"),
            "SYMBOL_OUT_OF_SCOPE",
        ),
        (
            evidence("1h"),
            replace(evidence("15m"), declared_symbol="ETHUSDT"),
            "PAIR_SYMBOL_MISMATCH",
        ),
        (replace(evidence("1h"), quality_passed=False), evidence("15m"), "IMAGE_QUALITY_FAILED"),
        (replace(evidence("1h"), ocr_symbol="ETHUSDT"), evidence("15m"), "OCR_SYMBOL_MISMATCH"),
        (replace(evidence("1h"), ocr_timeframe="15m"), evidence("15m"), "OCR_TIMEFRAME_MISMATCH"),
        (
            replace(evidence("1h"), capture_time_ms=NOW + 31_000),
            evidence("15m"),
            "CAPTURE_TIME_IN_FUTURE",
        ),
    ],
)
def test_structural_or_certain_conflicts_reject(
    one_hour: ImageEvidence, fifteen: ImageEvidence, reason: str
) -> None:
    assert decision(one_hour, fifteen) == (GateDecision.REJECTED_INPUT, (reason,))


@pytest.mark.parametrize(
    ("fifteen", "reason"),
    [
        (replace(evidence("15m"), capture_time_ms=NOW - 180_001), "PAIR_CAPTURE_TIME_MISMATCH"),
        (replace(evidence("15m"), capture_time_ms=NOW - 121_000), "STALE_IMAGE"),
        (replace(evidence("15m"), visible_last_price=Decimal("100.36")), "LAST_PRICE_MISMATCH"),
    ],
)
def test_temporal_and_market_context_fail_safe_to_no_trade(
    fifteen: ImageEvidence, reason: str
) -> None:
    one_hour = evidence("1h")
    assert decision(one_hour, fifteen) == (GateDecision.NO_TRADE, (reason,))


def test_low_confidence_ocr_does_not_override_declared_metadata() -> None:
    one_hour = replace(
        evidence("1h"),
        ocr_symbol="ETHUSDT",
        ocr_symbol_confidence=Decimal("0.89"),
        ocr_timeframe="15m",
        ocr_timeframe_confidence=Decimal("0.89"),
    )
    assert decision(one_hour, evidence("15m"))[0] is GateDecision.ACCEPT


def test_missing_price_is_allowed_but_invalid_authoritative_price_fails_closed() -> None:
    one_hour = replace(evidence("1h"), visible_last_price=None, authoritative_price=None)
    assert decision(one_hour, evidence("15m"))[0] is GateDecision.ACCEPT
    with pytest.raises(ValueError, match="positive"):
        decision(
            replace(one_hour, visible_last_price=Decimal(1), authoritative_price=Decimal(0)),
            evidence("15m"),
        )
