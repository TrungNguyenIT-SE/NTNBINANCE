from __future__ import annotations

from pathlib import Path

import pytest

from ntnbinance.features.config import FeatureConfig
from ntnbinance.features.coverage import evaluate_coverage
from ntnbinance.features.models import CoverageDecision, CoverageEvidence
from ntnbinance.features.registry import FEATURE_NAMES, FEATURE_REGISTRY


def test_registry_is_unique_complete_and_config_is_locked() -> None:
    assert len(FEATURE_NAMES) == len(set(FEATURE_NAMES)) == 20
    assert all(item.formula and item.window and item.missing_rule for item in FEATURE_REGISTRY)
    config = FeatureConfig.load(Path("configs/features/feature-set-v2.toml"))
    assert config.version == "2.0.0"
    assert config.optional_context.mark_index_basis
    assert not config.optional_context.funding
    assert not config.optional_context.open_interest


def test_invalid_config_is_rejected(tmp_path: Path) -> None:
    source = Path("configs/features/feature-set-v2.toml").read_text(encoding="utf-8")
    path = tmp_path / "invalid.toml"
    path.write_text(source.replace('version = "2.0.0"', 'version = "9.0.0"'), encoding="utf-8")
    with pytest.raises(ValueError, match="unsupported"):
        FeatureConfig.load(path)


def test_coverage_requires_percentage_and_meaningful_span() -> None:
    basis = evaluate_coverage(
        CoverageEvidence("basis", actual=100, expected=100, span_days=2),
        minimum_percent=99.9,
        minimum_span_days=1,
    )
    assert basis.decision is CoverageDecision.INCLUDE
    short_history = evaluate_coverage(
        CoverageEvidence("funding", actual=6, expected=6, span_days=2),
        minimum_percent=99,
        minimum_span_days=30,
    )
    assert short_history.decision is CoverageDecision.EXCLUDE
    assert short_history.reason_codes == ("HISTORY_SPAN_TOO_SHORT",)
    incomplete = evaluate_coverage(
        CoverageEvidence("oi", actual=90, expected=100, span_days=40),
        minimum_percent=99,
        minimum_span_days=30,
    )
    assert incomplete.reason_codes == ("COVERAGE_BELOW_THRESHOLD",)


def test_invalid_coverage_inputs_fail_closed() -> None:
    result = evaluate_coverage(
        CoverageEvidence("oi", actual=2, expected=1, span_days=0),
        minimum_percent=99,
        minimum_span_days=30,
    )
    assert result.decision is CoverageDecision.EXCLUDE
    assert "INVALID_COUNTS" in result.reason_codes
    with pytest.raises(ValueError, match="threshold"):
        evaluate_coverage(CoverageEvidence("oi", 1, 1, 1), minimum_percent=101, minimum_span_days=1)
