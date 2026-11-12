from pathlib import Path

import pytest

from ntnbinance.baselines.models import FEATURE_NAMES, BaselineConfig


def test_locked_baseline_config_loads() -> None:
    config = BaselineConfig.load(Path("configs/baselines/baseline-v1.toml"))

    assert config.seed == 20261113
    assert len(FEATURE_NAMES) == 13
    assert len(config.canonical_hash) == 64


def test_invalid_atr_rule_is_rejected(tmp_path: Path) -> None:
    source = Path("configs/baselines/baseline-v1.toml").read_text(encoding="utf-8")
    path = tmp_path / "invalid.toml"
    path.write_text(
        source.replace("minimum_atr_ratio = 0.001", "minimum_atr_ratio = 0.02"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ATR range"):
        BaselineConfig.load(path)
