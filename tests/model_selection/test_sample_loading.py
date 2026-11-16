from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from ntnbinance.baselines.models import BaselineSample
from ntnbinance.features.models import FeatureCandle, FeatureVector
from ntnbinance.labels.models import Label, LabelReason
from ntnbinance.model_selection import data
from ntnbinance.model_selection.models import ModelSelectionConfig
from ntnbinance.splits.models import Partition


def _sample(sample_id: str, partition: Partition, decision_time_ms: int) -> BaselineSample:
    return BaselineSample(
        sample_id=sample_id,
        partition=partition,
        symbol="BTCUSDT",
        decision_time_ms=decision_time_ms,
        vertical_barrier_time_ms=decision_time_ms + 900_000,
        label=Label.LONG,
        reason=LabelReason.UPPER_BARRIER_NET_POSITIVE,
        reference_price=100.0,
        upper_barrier=101.0,
        lower_barrier=99.0,
        barrier_time_ms=decision_time_ms + 1,
        execution_cost=0.001,
        funding_cost=0.0,
        vertical_close=101.0,
        features=(1.0,),
    )


def _candle(close_time_ms: int, interval: str) -> FeatureCandle:
    return FeatureCandle(
        dataset="trade_klines",
        symbol="BTCUSDT",
        interval=interval,
        close_time_ms=close_time_ms,
        event_time_ms=close_time_ms,
        open=Decimal("100"),
        high=Decimal("102"),
        low=Decimal("99"),
        close=Decimal("101"),
        volume_base=Decimal("10"),
    )


def test_sample_assembly_rejections_and_cache(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    samples = (
        _sample("train-ok", Partition.TRAIN, 10_000_000),
        _sample("validation-ok", Partition.VALIDATION, 11_000_000),
        _sample("train-missing", Partition.TRAIN, 12_000_000),
        _sample("validation-missing", Partition.VALIDATION, 13_000_000),
    )
    vectors = tuple(
        FeatureVector(
            version="2.0.0",
            symbol=sample.symbol,
            decision_time_ms=sample.decision_time_ms,
            names=("feature",),
            values=(float(index),),
            max_event_time_ms=sample.decision_time_ms - 1,
            lineage=(("trade_klines", sample.decision_time_ms - 1),),
        )
        for index, sample in enumerate(samples[:2])
    )
    candles_15m = tuple(_candle(index * 900_000, "15m") for index in range(1, 10))
    candles_1h = tuple(_candle(index * 3_600_000, "1h") for index in range(1, 3))
    groups = {
        ("trade_klines", "BTCUSDT", "15m"): candles_15m,
        ("trade_klines", "BTCUSDT", "1h"): candles_1h,
    }
    monkeypatch.setattr(data, "load_development_samples", lambda **_kwargs: (samples, 26))
    monkeypatch.setattr(data, "development_feature_vectors", lambda _root: vectors)
    monkeypatch.setattr(data, "load_clean_candles", lambda _root: groups)
    monkeypatch.setattr(data, "_chart_embedding", lambda *_args, **_kwargs: (0.1, 0.2))

    image_config = ModelSelectionConfig.load(Path("configs/models/model-selection-v1.toml")).image
    cache_path = tmp_path / "cache" / "samples.joblib"
    loaded = data.load_model_samples(
        split_path=tmp_path / "split.json",
        labels_path=tmp_path / "labels.jsonl",
        clean_root=tmp_path / "clean",
        label_run_id="run",
        execution_cost=0.001,
        image_config=image_config,
        cache_path=cache_path,
        cache_key="locked",
    )
    assert [item.baseline.sample_id for item in loaded.samples] == ["train-ok", "validation-ok"]
    assert loaded.rejected_train_missing_features == 1
    assert loaded.rejected_validation_missing_features == 1
    assert loaded.sealed_holdout_rows == 26
    assert cache_path.is_file()

    monkeypatch.setattr(
        data, "load_development_samples", lambda **_kwargs: (_ for _ in ()).throw(AssertionError)
    )
    assert (
        data.load_model_samples(
            split_path=tmp_path / "split.json",
            labels_path=tmp_path / "labels.jsonl",
            clean_root=tmp_path / "clean",
            label_run_id="run",
            execution_cost=0.001,
            image_config=image_config,
            cache_path=cache_path,
            cache_key="locked",
        )
        == loaded
    )
