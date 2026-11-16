from __future__ import annotations

from pathlib import Path

import pytest

from ntnbinance.model_selection.models import ModelSelectionConfig
from ntnbinance.model_selection.pipeline import choose_champion

CONFIG_PATH = Path("configs/models/model-selection-v1.toml")


def _result(macro_f1: float, *, passed: bool = True) -> dict[str, object]:
    return {
        "classification": {
            "macro_f1": macro_f1,
            "accuracy": macro_f1,
            "multiclass_brier": 1 - macro_f1,
        },
        "resource_passed": passed,
    }


def test_config_is_locked_and_content_addressed() -> None:
    config = ModelSelectionConfig.load(CONFIG_PATH)
    assert config.seed == 20261116
    assert config.feature_version == "2.0.0"
    assert len(config.canonical_hash) == 64


def test_invalid_config_is_rejected(tmp_path: Path) -> None:
    text = CONFIG_PATH.read_text(encoding="utf-8")
    target = tmp_path / "bad.toml"
    target.write_text(text.replace("n_jobs = 1", "n_jobs = 2"), encoding="utf-8")
    with pytest.raises(ValueError, match="deterministic"):
        ModelSelectionConfig.load(target)


def test_vision_is_discarded_when_gain_is_not_meaningful() -> None:
    config = ModelSelectionConfig.load(CONFIG_PATH)
    champion, reason = choose_champion(
        {
            "numeric_xgboost": _result(0.50),
            "image_logistic": _result(0.60),
            "fusion_xgboost": _result(0.515),
        },
        config,
    )
    assert champion == "numeric_xgboost"
    assert "vision gain" in reason


def test_meaningful_fusion_gain_is_selected() -> None:
    config = ModelSelectionConfig.load(CONFIG_PATH)
    champion, _ = choose_champion(
        {
            "numeric_logistic": _result(0.49),
            "fusion_logistic": _result(0.54),
        },
        config,
    )
    assert champion == "fusion_logistic"


def test_exit_gate_rejects_weak_or_oversized_candidates() -> None:
    config = ModelSelectionConfig.load(CONFIG_PATH)
    with pytest.raises(RuntimeError, match="locked requirement"):
        choose_champion(
            {
                "numeric_logistic": _result(0.46),
                "fusion_xgboost": _result(0.70, passed=False),
                "image_logistic": _result(0.90),
            },
            config,
        )
