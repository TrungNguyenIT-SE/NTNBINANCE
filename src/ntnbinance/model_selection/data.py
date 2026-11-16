"""Leakage-safe numeric and synthetic-image sample assembly."""

from __future__ import annotations

import time
from decimal import Decimal
from pathlib import Path

import joblib
import numpy as np
from PIL import Image

from ntnbinance.baselines.data import load_development_samples
from ntnbinance.features.audit import development_feature_vectors, load_clean_candles
from ntnbinance.features.models import FeatureCandle
from ntnbinance.image_pipeline.models import Candle
from ntnbinance.image_pipeline.quality import measure_quality
from ntnbinance.image_pipeline.renderer import render_chart
from ntnbinance.model_selection.models import (
    ImageConfig,
    LoadedModelSamples,
    ModelSample,
)
from ntnbinance.splits.models import Partition


def _visible(
    records: tuple[FeatureCandle, ...], decision_time_ms: int
) -> tuple[FeatureCandle, ...]:
    return tuple(
        item
        for item in records
        if item.is_closed
        and item.event_time_ms < decision_time_ms
        and item.close_time_ms < decision_time_ms
    )


def _render_candles(records: tuple[FeatureCandle, ...], interval_ms: int) -> tuple[Candle, ...]:
    return tuple(
        Candle(
            open_time_ms=item.close_time_ms - interval_ms + 1,
            close_time_ms=item.close_time_ms,
            open=item.open,
            high=item.high,
            low=item.low,
            close=item.close,
            volume=item.volume_base or Decimal(0),
        )
        for item in records[-120:]
    )


def _chart_embedding(
    records: tuple[FeatureCandle, ...],
    *,
    symbol: str,
    timeframe: str,
    decision_time_ms: int,
    config: ImageConfig,
) -> tuple[float, ...]:
    interval_ms = 900_000 if timeframe == "15m" else 3_600_000
    chart = render_chart(
        _render_candles(records, interval_ms),
        symbol=symbol,
        timeframe=timeframe,
        decision_time_ms=decision_time_ms,
        theme=config.theme,
        size=(config.width, config.height),
    )
    # Exclude title, OCR text and axes; encode only the chart plot.
    plot = chart.crop(
        (
            round(chart.width * 0.055),
            round(chart.height * 0.14),
            round(chart.width * 0.90),
            round(chart.height * 0.84),
        )
    )
    reduced = plot.convert("L").resize(
        (config.embedding_width, config.embedding_height), Image.Resampling.BILINEAR
    )
    pixels = np.asarray(reduced, dtype=np.float64).reshape(-1) / 255.0
    quality = measure_quality(chart, timeframe=timeframe)
    quality_values = np.asarray(
        [
            quality.blur_score / 1000,
            quality.contrast_score,
            quality.edge_density,
            quality.candle_components / 200,
            quality.right_axis_score,
            quality.bottom_axis_score,
            quality.occlusion_fraction,
            1.0 if quality.chart_detected else 0.0,
            1.0 if quality.decision.value == "ACCEPT" else 0.0,
        ],
        dtype=np.float64,
    )
    return tuple(np.concatenate((pixels, quality_values)).tolist())


def load_model_samples(
    *,
    split_path: Path,
    labels_path: Path,
    clean_root: Path,
    label_run_id: str,
    execution_cost: float,
    image_config: ImageConfig,
    cache_path: Path | None = None,
    cache_key: str | None = None,
) -> LoadedModelSamples:
    if cache_path is not None and cache_path.is_file():
        cached = joblib.load(cache_path)
        if isinstance(cached, dict) and cached.get("key") == cache_key:
            loaded = cached.get("samples")
            if isinstance(loaded, LoadedModelSamples):
                return loaded
    baseline_samples, sealed = load_development_samples(
        split_path=split_path,
        labels_path=labels_path,
        clean_root=clean_root,
        label_run_id=label_run_id,
        execution_cost=execution_cost,
    )
    numeric = {
        (item.symbol, item.decision_time_ms): item
        for item in development_feature_vectors(clean_root)
    }
    groups = load_clean_candles(clean_root)
    result: list[ModelSample] = []
    rejected_train = 0
    rejected_validation = 0
    started = time.perf_counter()
    for sample in baseline_samples:
        key = (sample.symbol, sample.decision_time_ms)
        vector = numeric.get(key)
        if vector is None:
            if sample.partition is Partition.TRAIN:
                rejected_train += 1
            elif sample.partition is Partition.VALIDATION:
                rejected_validation += 1
            continue
        trade_15m = _visible(
            groups[("trade_klines", sample.symbol, "15m")], sample.decision_time_ms
        )
        trade_1h = _visible(groups[("trade_klines", sample.symbol, "1h")], sample.decision_time_ms)
        image_15m = _chart_embedding(
            trade_15m,
            symbol=sample.symbol,
            timeframe="15m",
            decision_time_ms=sample.decision_time_ms,
            config=image_config,
        )
        image_1h = _chart_embedding(
            trade_1h,
            symbol=sample.symbol,
            timeframe="1h",
            decision_time_ms=sample.decision_time_ms,
            config=image_config,
        )
        result.append(ModelSample(sample, vector.values, (*image_1h, *image_15m)))
    elapsed_ms = (time.perf_counter() - started) * 1000
    loaded = LoadedModelSamples(
        tuple(result), sealed, elapsed_ms, rejected_train, rejected_validation
    )
    if cache_path is not None:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(".joblib.tmp")
        joblib.dump({"key": cache_key, "samples": loaded}, temporary, compress=3)
        temporary.replace(cache_path)
    return loaded
