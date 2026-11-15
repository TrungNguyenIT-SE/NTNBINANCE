from __future__ import annotations

from dataclasses import replace

import pytest

from ntnbinance.image_pipeline.augment import augment_for_training
from ntnbinance.image_pipeline.models import Candle
from ntnbinance.image_pipeline.renderer import image_sha256, render_chart

from .conftest import DECISION_TIME_MS


@pytest.mark.parametrize("theme", ["DARK", "LIGHT", "ALT"])
@pytest.mark.parametrize("layout", ["SYNTHETIC", "BINANCE_LIKE", "TRADINGVIEW_LIKE"])
def test_renderer_is_deterministic_across_theme_and_layout(
    candles: tuple[Candle, ...], theme: str, layout: str
) -> None:
    assert image_sha256(
        render_chart(
            candles,
            symbol="ETHUSDT",
            timeframe="15m",
            decision_time_ms=DECISION_TIME_MS,
            theme=theme,
            source_layout=layout,
        )
    ) == image_sha256(
        render_chart(
            candles,
            symbol="ETHUSDT",
            timeframe="15m",
            decision_time_ms=DECISION_TIME_MS,
            theme=theme,
            source_layout=layout,
        )
    )


@pytest.mark.parametrize(
    ("candles_override", "kwargs", "message"),
    [
        ((), {}, "at least one"),
        (None, {"symbol": "SOLUSDT"}, "unsupported symbol"),
        (None, {"timeframe": "5m"}, "unsupported symbol"),
        (None, {"theme": "NEON"}, "unsupported render theme"),
        (None, {"size": (700, 500)}, "below the image contract"),
    ],
)
def test_renderer_rejects_invalid_contract(
    candles: tuple[Candle, ...],
    candles_override: tuple[Candle, ...] | None,
    kwargs: dict[str, object],
    message: str,
) -> None:
    arguments: dict[str, object] = {
        "symbol": "ETHUSDT",
        "timeframe": "15m",
        "decision_time_ms": DECISION_TIME_MS,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=message):
        render_chart(candles if candles_override is None else candles_override, **arguments)  # type: ignore[arg-type]


def test_renderer_rejects_unsorted_and_future_candles(candles: tuple[Candle, ...]) -> None:
    with pytest.raises(ValueError, match="ordered"):
        render_chart(
            tuple(reversed(candles)),
            symbol="ETHUSDT",
            timeframe="15m",
            decision_time_ms=DECISION_TIME_MS,
        )
    future = (*candles[:-1], replace(candles[-1], close_time_ms=DECISION_TIME_MS + 1))
    with pytest.raises(ValueError, match="after decision_time"):
        render_chart(
            future,
            symbol="ETHUSDT",
            timeframe="15m",
            decision_time_ms=DECISION_TIME_MS,
        )


def test_augmentation_is_train_only_deterministic_and_keeps_orientation(
    candles: tuple[Candle, ...],
) -> None:
    image = render_chart(
        candles,
        symbol="ETHUSDT",
        timeframe="15m",
        decision_time_ms=DECISION_TIME_MS,
    )
    first = augment_for_training(image, partition="TRAIN", seed=42)
    second = augment_for_training(image, partition="TRAIN", seed=42)
    assert first.tobytes() == second.tobytes()
    assert first.size == image.size
    with pytest.raises(PermissionError, match="TRAIN"):
        augment_for_training(image, partition="VALIDATION", seed=42)
