from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from ntnbinance.features.models import FeatureCandle
from ntnbinance.model_selection.data import _chart_embedding, _visible
from ntnbinance.model_selection.models import ModelSelectionConfig


def _candle(index: int, event_time_ms: int | None = None) -> FeatureCandle:
    close_time = (index + 1) * 900_000
    close = Decimal(100 + index % 7)
    return FeatureCandle(
        dataset="trade_klines",
        symbol="BTCUSDT",
        interval="15m",
        close_time_ms=close_time,
        event_time_ms=close_time if event_time_ms is None else event_time_ms,
        open=close - 1,
        high=close + 2,
        low=close - 2,
        close=close,
        volume_base=Decimal(1000 + index),
        trade_count=100 + index,
        taker_buy_volume_base=Decimal(500),
    )


def test_image_embedding_is_deterministic_and_header_free() -> None:
    config = ModelSelectionConfig.load(Path("configs/models/model-selection-v1.toml")).image
    records = tuple(_candle(index) for index in range(40))
    decision = records[-1].close_time_ms + 1
    first = _chart_embedding(
        records,
        symbol="BTCUSDT",
        timeframe="15m",
        decision_time_ms=decision,
        config=config,
    )
    second = _chart_embedding(
        records,
        symbol="BTCUSDT",
        timeframe="15m",
        decision_time_ms=decision,
        config=config,
    )
    assert first == second
    assert len(first) == config.embedding_width * config.embedding_height + 9

    future = _candle(99, event_time_ms=decision + 1)
    assert _visible((*records, future), decision) == records
