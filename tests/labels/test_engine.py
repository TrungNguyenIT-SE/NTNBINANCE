from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from ntnbinance.data_contract import QualityFlag
from ntnbinance.labels.engine import calculate_atr, label_sample
from ntnbinance.labels.models import FundingEvent, Label, LabelReason, LabelResult

from .helpers import config, sample_window, touched


def _label(
    *,
    touch_index: int | None = None,
    high: str = "101",
    low: str = "99",
    funding: list[FundingEvent] | None = None,
    small_atr: bool = False,
) -> LabelResult:
    history, future, intrabars = sample_window(
        history_high="100.05" if small_atr else "101",
        history_low="99.95" if small_atr else "99",
    )
    if touch_index is not None:
        intrabars[touch_index] = touched(intrabars[touch_index], high=high, low=low)
    return label_sample(
        history=history,
        future=future,
        intrabars=intrabars,
        funding_events=funding or [],
        config=config(),
    )


def test_atr_and_long_label_are_hand_calculable() -> None:
    history, _, _ = sample_window()
    assert calculate_atr(history, 14) == Decimal("2")
    result = _label(touch_index=1, high="102", low="99")
    assert result.label is Label.LONG
    assert result.reason is LabelReason.UPPER_BARRIER_NET_POSITIVE
    assert result.upper_barrier == Decimal("102.0")
    assert result.lower_barrier == Decimal("98.0")
    assert result.gross_return == Decimal("0.02")
    assert result.execution_cost == Decimal("0.00135")
    assert result.net_return == Decimal("0.01865")


def test_short_label_and_positive_funding_receipt() -> None:
    _, _, intrabars = sample_window()
    event_time = intrabars[0].close_time_ms
    result = _label(
        touch_index=2,
        high="101",
        low="98",
        funding=[FundingEvent("BTCUSDT", event_time, Decimal("0.0001"), "funding")],
    )
    assert result.label is Label.SHORT
    assert result.funding_cost == Decimal("-0.0001")
    assert result.net_return == Decimal("0.01875")


def test_long_pays_positive_funding_only_when_position_crosses_settlement() -> None:
    _, _, intrabars = sample_window()
    event_time = intrabars[0].close_time_ms
    result = _label(
        touch_index=2,
        high="102",
        funding=[FundingEvent("BTCUSDT", event_time, Decimal("0.0001"), "funding")],
    )
    assert result.funding_cost == Decimal("0.0001")
    assert result.net_return == Decimal("0.01855")


def test_same_one_minute_bar_is_ambiguous_no_trade() -> None:
    result = _label(touch_index=0, high="102", low="98")
    assert result.label is Label.NO_TRADE
    assert result.reason is LabelReason.AMBIGUOUS_INTRABAR


def test_distinct_intrabar_order_resolves_dual_15m_touch() -> None:
    history, future, intrabars = sample_window()
    future[0] = touched(future[0], high="102", low="98")
    intrabars[2] = touched(intrabars[2], high="102")
    intrabars[5] = touched(intrabars[5], low="98")
    result = label_sample(
        history=history,
        future=future,
        intrabars=intrabars,
        funding_events=[],
        config=config(),
    )
    assert result.label is Label.LONG


def test_no_touch_reaches_vertical_barrier() -> None:
    result = _label()
    assert result.label is Label.NO_TRADE
    assert result.reason is LabelReason.VERTICAL_BARRIER
    assert result.barrier_time_ms is None


def test_data_after_vertical_barrier_cannot_change_label() -> None:
    history, future, intrabars = sample_window()
    after = replace(
        intrabars[-1],
        open_time_ms=intrabars[-1].open_time_ms + 60_000,
        close_time_ms=intrabars[-1].close_time_ms + 60_000,
        high=Decimal("1000"),
        low=Decimal("1"),
        raw_identity="after-vertical",
    )
    result = label_sample(
        history=history,
        future=future,
        intrabars=[*intrabars, after],
        funding_events=[
            FundingEvent(
                "BTCUSDT",
                future[-1].close_time_ms + 60_000,
                Decimal("0.5"),
                "future-funding",
            )
        ],
        config=config(),
    )
    assert result.label is Label.NO_TRADE
    assert result.reason is LabelReason.VERTICAL_BARRIER
    assert "after-vertical" not in result.source_identities
    assert "future-funding" not in result.source_identities


def test_cost_can_remove_small_gross_edge() -> None:
    result = _label(touch_index=0, high="100.1", low="99.95", small_atr=True)
    assert result.label is Label.NO_TRADE
    assert result.reason is LabelReason.COST_REMOVED_EDGE
    assert result.gross_return == Decimal("0.001")
    assert result.net_return == Decimal("-0.00035")


def test_quality_flag_or_incomplete_intrabar_window_fails_safe() -> None:
    history, future, intrabars = sample_window()
    history[-1] = history[-1].add_flags(QualityFlag.CLOCK_SKEW)
    result = label_sample(
        history=history,
        future=future,
        intrabars=intrabars,
        funding_events=[],
        config=config(),
    )
    assert result.label is Label.NO_TRADE
    assert result.reason is LabelReason.DATA_QUALITY

    result = label_sample(
        history=sample_window()[0],
        future=future,
        intrabars=intrabars[:-1],
        funding_events=[],
        config=config(),
    )
    assert result.reason is LabelReason.DATA_QUALITY


def test_wrong_window_lengths_or_noncontiguous_future_are_rejected() -> None:
    history, future, intrabars = sample_window()
    with pytest.raises(ValueError, match="history length"):
        label_sample(
            history=history[:-1],
            future=future,
            intrabars=intrabars,
            funding_events=[],
            config=config(),
        )
    future[1] = replace(future[1], open_time_ms=future[1].open_time_ms + 1)
    with pytest.raises(ValueError, match="contiguous"):
        label_sample(
            history=history,
            future=future,
            intrabars=intrabars,
            funding_events=[],
            config=config(),
        )


def test_noncontiguous_history_and_cross_symbol_funding_are_rejected_or_ignored() -> None:
    history, future, intrabars = sample_window()
    broken = [*history]
    broken[1] = replace(broken[1], open_time_ms=broken[1].open_time_ms + 1)
    with pytest.raises(ValueError, match="ATR history must be contiguous"):
        label_sample(
            history=broken,
            future=future,
            intrabars=intrabars,
            funding_events=[],
            config=config(),
        )

    intrabars[2] = touched(intrabars[2], high="102")
    result = label_sample(
        history=history,
        future=future,
        intrabars=intrabars,
        funding_events=[
            FundingEvent(
                "ETHUSDT",
                intrabars[0].close_time_ms,
                Decimal("0.5"),
                "wrong-symbol",
            )
        ],
        config=config(),
    )
    assert result.label is Label.LONG
    assert result.funding_cost == 0
    assert "wrong-symbol" not in result.source_identities
