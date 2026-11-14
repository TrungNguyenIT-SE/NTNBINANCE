from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest

from ntnbinance.backtest import data
from ntnbinance.backtest.models import MinuteCandle
from ntnbinance.baselines.models import FEATURE_NAMES
from ntnbinance.labels.models import LabelConfig


def test_validation_loader_is_label_blind(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    split = tmp_path / "split.json"
    split.write_text(
        json.dumps(
            {
                "assignments": {
                    "sample": {
                        "partition": "VALIDATION",
                        "symbol": "BTCUSDT",
                        "decision_time_ms": 1_000_000,
                        "vertical_barrier_time_ms": 4_600_000,
                    },
                    "sealed": {
                        "partition": "FINAL_HOLDOUT",
                        "symbol": "BTCUSDT",
                        "decision_time_ms": 5_000_000,
                        "vertical_barrier_time_ms": 8_600_000,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    groups = {("trade_klines", "BTCUSDT", "15m"): [{"time": 999_999, "close": 100.0}]}
    features = [0.0] * len(FEATURE_NAMES)
    features[FEATURE_NAMES.index("atr_ratio_14")] = 0.004
    minutes = [
        MinuteCandle(
            "BTCUSDT",
            1_000_000 + index * 60_000,
            1_059_999 + index * 60_000,
            Decimal(100),
            Decimal(101),
            Decimal(99),
            Decimal(100),
            Decimal(10),
        )
        for index in range(60)
    ]
    monkeypatch.setattr(data, "load_feature_candles", lambda _: groups)
    monkeypatch.setattr(data, "build_features", lambda *_: tuple(features))
    monkeypatch.setattr(data, "_load_minutes", lambda _: {"BTCUSDT": minutes})
    monkeypatch.setattr(data, "load_funding_events", lambda _: [])

    inputs = data.load_validation_inputs(
        split_path=split,
        clean_root=tmp_path,
        raw_root=tmp_path,
        label_config=LabelConfig.load(Path("configs/labels/triple-barrier-v1.toml")),
    )

    assert len(inputs) == 1
    assert inputs[0].sample_id == "sample"
    assert inputs[0].atr == Decimal("0.4000")
    assert inputs[0].regime.value == "NORMAL"
