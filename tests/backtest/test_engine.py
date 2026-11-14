from dataclasses import replace
from decimal import Decimal

import pytest

from ntnbinance.backtest.engine import simulate_trade
from ntnbinance.backtest.models import ExitReason, FillStatus, Side
from ntnbinance.labels.models import FundingEvent

from .helpers import candle, case, config


def test_long_hand_calculation_uses_post_latency_open_and_funding() -> None:
    candles = (
        candle(0, open_price="50", high="51", low="49", close="50"),
        candle(1, high="103", low="99"),
    )
    funding = (FundingEvent("BTCUSDT", 100_000, Decimal("0.001"), "funding"),)

    result = simulate_trade(case(candles, funding=funding), config())

    assert result.entry_time_ms == 60_000
    assert result.raw_entry_price == Decimal("100")
    assert result.exit_reason is ExitReason.TAKE_PROFIT
    assert result.raw_exit_price == Decimal("102")
    assert result.gross_pnl_usdt == Decimal("2.0")
    assert result.fee_cost_usdt == Decimal("0.2020")
    assert result.funding_cost_usdt == Decimal("0.1000")
    assert result.net_pnl_usdt == Decimal("1.6980")


def test_same_minute_dual_touch_is_stop_first_for_short() -> None:
    candles = (candle(1, high="103", low="97"),)

    result = simulate_trade(case(candles, side=Side.SHORT), config())

    assert result.exit_reason is ExitReason.STOP_LOSS
    assert result.raw_exit_price == Decimal("102")
    assert result.net_pnl_usdt < 0


def test_tick_step_partial_and_unfilled_rules() -> None:
    partial = simulate_trade(case((candle(1, open_price="100.03", volume="0.55"),)), config())
    unfilled = simulate_trade(case((candle(1, open_price="100.03", volume="0.05"),)), config())

    assert partial.entry_fill_price == Decimal("100.1")
    assert partial.requested_quantity == Decimal("0.9")
    assert partial.filled_quantity == Decimal("0.5")
    assert partial.fill_status is FillStatus.PARTIALLY_FILLED
    assert unfilled.fill_status is FillStatus.UNFILLED
    assert unfilled.filled_quantity == 0


def test_abstain_missing_candle_and_invalid_stress_fail_closed() -> None:
    abstain = simulate_trade(case((), side=Side.NO_TRADE), config())
    missing = simulate_trade(case(()), config())

    assert abstain.fill_status is FillStatus.NO_TRADE
    assert missing.fill_status is FillStatus.UNFILLED
    with pytest.raises(ValueError, match="cannot be negative"):
        simulate_trade(case(()), config(), latency_ms=-1)


def test_higher_cost_reduces_same_trade_net_pnl() -> None:
    candles = (candle(1, high="103", low="99"),)
    local_config = replace(
        config(),
        half_spread_bps_per_side=Decimal("1"),
        slippage_bps_per_side=Decimal("1"),
    )

    base = simulate_trade(case(candles), local_config)
    stressed = simulate_trade(case(candles), local_config, cost_multiplier=Decimal("2"))

    assert stressed.net_pnl_usdt < base.net_pnl_usdt
    assert stressed.fee_cost_usdt > base.fee_cost_usdt
