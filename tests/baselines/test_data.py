from __future__ import annotations

import json
from pathlib import Path

import pytest

from ntnbinance.baselines import data


def test_final_holdout_target_is_not_deserialized(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    label_run = "locked-run"
    symbol = "BTCUSDT"
    decision = 123456
    config_hash = "a" * 64
    identifier = data.sample_id(label_run, symbol, decision, config_hash)
    split = tmp_path / "split.json"
    split.write_text(
        json.dumps(
            {
                "assignments": {
                    identifier: {
                        "partition": "FINAL_HOLDOUT",
                        "symbol": symbol,
                        "decision_time_ms": decision,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    labels = tmp_path / "labels.jsonl"
    # Deliberately invalid JSON after the identity fields: json.loads would fail.
    labels.write_text(
        f'{{"config_hash":"{config_hash}","decision_time_ms":{decision},'
        f'"symbol":"{symbol}","label":BROKEN}}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(data, "_load_candles", lambda _: {})

    samples, sealed = data.load_development_samples(
        split_path=split,
        labels_path=labels,
        clean_root=tmp_path,
        label_run_id=label_run,
        execution_cost=0.00135,
    )

    assert samples == []
    assert sealed == 1


def test_sample_identity_is_content_addressed() -> None:
    first = data.sample_id("run", "BTCUSDT", 1, "a" * 64)
    assert first == data.sample_id("run", "BTCUSDT", 1, "a" * 64)
    assert first != data.sample_id("run", "ETHUSDT", 1, "a" * 64)


def test_point_in_time_features_use_only_closed_history() -> None:
    def candle(time: int, close: float, volume: float = 10.0) -> dict[str, float | int]:
        return {
            "time": time,
            "open": close - 0.2,
            "high": close + 0.5,
            "low": close - 0.5,
            "close": close,
            "volume": volume,
            "taker": volume * 0.55,
        }

    symbol = "BTCUSDT"
    trade = [candle(index, 100.0 + index * 0.1, 10.0 + index) for index in range(15)]
    # A future outlier must be ignored by the decision-time filter.
    trade.append(candle(100, 9999.0))
    groups = {
        ("trade_klines", symbol, "15m"): trade,
        ("trade_klines", symbol, "1h"): [
            candle(1, 100.0),
            candle(5, 101.0),
            candle(9, 102.0),
        ],
        ("mark_price_klines", symbol, "15m"): [candle(14, 101.5)],
        ("index_price_klines", symbol, "15m"): [candle(14, 101.3)],
    }

    features = data._features(groups, symbol, 20)

    assert len(features) == 13
    assert features[0] < 0.01
    assert features[-1] == 0.0
