from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal

import pytest

from ntnbinance.data_contract import QualityFlag
from ntnbinance.labels.models import LabelConfig

from .helpers import config


def test_versioned_config_has_stable_hash_and_cost() -> None:
    first = config()
    second = config()
    assert first.canonical_hash == second.canonical_hash
    assert len(first.canonical_hash) == 64
    assert first.fixed_execution_cost == Decimal("0.00135")
    assert first.horizon_bars == 4
    assert first.secondary_horizons == (2, 8)
    assert QualityFlag.CLOCK_SKEW in first.disallowed_quality_flags


def test_invalid_config_fails_closed() -> None:
    mutations: tuple[Callable[[], LabelConfig], ...] = (
        lambda: replace(config(), version="2.0.0"),
        lambda: replace(config(), price_dataset="mark_price_klines"),
        lambda: replace(config(), intrabar_interval="5m"),
        lambda: replace(config(), atr_window=1),
        lambda: replace(config(), barrier_atr_multiplier=Decimal(0)),
        lambda: replace(config(), latency_ms=-1),
        lambda: replace(config(), low_volatility_atr_ratio=Decimal("0.01")),
        lambda: replace(config(), same_intrabar_policy="UPPER_FIRST"),
    )
    for mutate in mutations:
        with pytest.raises(ValueError, match=r".+"):
            mutate()
