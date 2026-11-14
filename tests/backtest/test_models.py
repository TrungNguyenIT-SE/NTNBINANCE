from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from ntnbinance.backtest.models import BacktestConfig, InstrumentRules


def test_locked_config_and_exchange_constraints_load() -> None:
    config = BacktestConfig.load(Path("configs/backtest/backtest-v1.toml"))

    assert config.instruments["BTCUSDT"].price_tick_size == Decimal("0.10")
    assert config.instruments["ETHUSDT"].min_notional == Decimal("20")
    assert config.cost_multipliers == (Decimal("1.0"), Decimal("1.5"), Decimal("2.0"))
    assert config.exchange_snapshot_manifest.endswith("exchange-info-stage-j.json")
    assert len(config.canonical_hash) == 64


def test_invalid_config_and_instrument_rules_are_rejected() -> None:
    config = BacktestConfig.load(Path("configs/backtest/backtest-v1.toml"))
    with pytest.raises(ValueError, match="cost stress"):
        replace(config, cost_multipliers=(Decimal("1.5"),))._validate()
    with pytest.raises(ValueError, match="snapshot manifest"):
        replace(config, exchange_snapshot_manifest="snapshot.txt")._validate()
    with pytest.raises(ValueError, match="positive"):
        InstrumentRules(Decimal(0), Decimal(1), Decimal(1), Decimal(2), Decimal(1))
