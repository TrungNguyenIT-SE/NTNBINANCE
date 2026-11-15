from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from ntnbinance.features.engine import build_feature_vector
from ntnbinance.features.registry import FEATURE_NAMES

from .helpers import DECISION_TIME_MS, candle, feature_input


def test_hand_calculated_feature_vector_and_lineage() -> None:
    data = feature_input()
    vector = build_feature_vector(data)
    values = vector.as_dict()
    assert vector.names == FEATURE_NAMES
    assert len(vector.values) == 20
    assert values["return_15m_1"] == pytest.approx(129 / 128 - 1)
    assert values["range_ratio_15m"] == pytest.approx(2 / 129)
    assert values["body_ratio_15m"] == pytest.approx(0.4 / 129)
    assert values["upper_wick_ratio_15m"] == pytest.approx(1 / 129)
    assert values["lower_wick_ratio_15m"] == pytest.approx(0.6 / 129)
    assert values["taker_buy_ratio"] == pytest.approx(79 / 129)
    assert values["mark_trade_basis"] == pytest.approx(0.1 / 129)
    assert values["index_trade_basis"] == pytest.approx(-0.1 / 129)
    assert values["symbol_is_eth"] == 0
    assert vector.max_event_time_ms < vector.decision_time_ms
    assert all(event_time < vector.decision_time_ms for _, event_time in vector.lineage)


def test_future_records_never_change_features() -> None:
    data = feature_input()
    expected = build_feature_vector(data)
    future = candle(
        99,
        close=Decimal("999999"),
        event_time_ms=DECISION_TIME_MS + 1000,
    )
    mutated = replace(data, trade_15m=(*data.trade_15m, future))
    assert build_feature_vector(mutated).values == expected.values


def test_event_time_at_decision_is_not_visible() -> None:
    data = feature_input()
    latest = replace(data.trade_15m[-1], event_time_ms=DECISION_TIME_MS)
    previous = data.trade_15m[-2]
    mark = candle(28, dataset="mark_price_klines", close=previous.close)
    index = candle(28, dataset="index_price_klines", close=previous.close)
    values = build_feature_vector(
        replace(
            data,
            trade_15m=(*data.trade_15m[:-1], latest),
            mark_15m=(mark, *data.mark_15m),
            index_15m=(index, *data.index_15m),
        )
    ).as_dict()
    assert values["return_15m_1"] == pytest.approx(128 / 127 - 1)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_volume", "required volume"),
        ("negative_volume", "non-negative"),
        ("taker_excess", "exceeds"),
        ("invalid_ohlc", "OHLC"),
        ("duplicate", "duplicate"),
        ("missing_basis", "aligned mark"),
    ],
)
def test_invalid_or_missing_inputs_fail_closed(mutation: str, message: str) -> None:
    data = feature_input()
    latest = data.trade_15m[-1]
    if mutation == "missing_volume":
        data = replace(data, trade_15m=(*data.trade_15m[:-1], replace(latest, volume_base=None)))
    elif mutation == "negative_volume":
        data = replace(
            data, trade_15m=(*data.trade_15m[:-1], replace(latest, volume_base=Decimal(-1)))
        )
    elif mutation == "taker_excess":
        data = replace(
            data,
            trade_15m=(*data.trade_15m[:-1], replace(latest, taker_buy_volume_base=Decimal(999))),
        )
    elif mutation == "invalid_ohlc":
        data = replace(data, trade_15m=(*data.trade_15m[:-1], replace(latest, high=Decimal(1))))
    elif mutation == "duplicate":
        data = replace(data, trade_15m=(*data.trade_15m, latest))
    else:
        data = replace(data, mark_15m=())
    with pytest.raises(ValueError, match=message):
        build_feature_vector(data)


def test_zero_activity_uses_documented_neutral_rules() -> None:
    data = feature_input()
    zeroed = tuple(
        replace(item, volume_base=Decimal(0), taker_buy_volume_base=Decimal(0), trade_count=0)
        for item in data.trade_15m
    )
    values = build_feature_vector(replace(data, trade_15m=zeroed)).as_dict()
    assert values["volume_ratio_4"] == 0
    assert values["volume_zscore_20"] == 0
    assert values["taker_buy_ratio"] == 0
    assert values["trade_count_ratio_4"] == 0


def test_eth_identity_and_input_scope() -> None:
    assert build_feature_vector(feature_input(symbol="ETHUSDT")).as_dict()["symbol_is_eth"] == 1
    with pytest.raises(ValueError, match="unsupported"):
        build_feature_vector(replace(feature_input(), symbol="SOLUSDT"))
    data = feature_input()
    with pytest.raises(ValueError, match="insufficient"):
        build_feature_vector(replace(data, trade_15m=data.trade_15m[-10:]))
