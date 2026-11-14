from dataclasses import replace

import pytest

from ntnbinance.backtest.engine import simulate_trade
from ntnbinance.backtest.metrics import grouped_metrics, summarize
from ntnbinance.backtest.models import Side

from .helpers import candle, case, config


def test_portfolio_and_group_metrics_are_complete() -> None:
    local_config = config()
    winner = simulate_trade(case((candle(1, high="103", low="99"),)), local_config)
    loser_case = replace(case((candle(1, high="101", low="97"),)), sample_id="loss")
    loser = simulate_trade(loser_case, local_config)
    abstain_case = replace(case((), side=Side.NO_TRADE), sample_id="none", decision_time_ms=60_000)
    abstain = simulate_trade(abstain_case, local_config)

    metrics = summarize([winner, loser, abstain], local_config)
    groups = grouped_metrics([winner, loser, abstain], local_config, lambda item: item.side.value)

    assert metrics.samples == 3
    assert metrics.filled_trades == 2
    assert metrics.profit_factor is not None
    assert metrics.maximum_drawdown_usdt > 0
    assert metrics.sharpe_annualized is not None
    assert metrics.sortino_annualized is not None
    assert set(groups) == {"LONG", "NO_TRADE"}
    assert groups["NO_TRADE"].net_pnl_usdt == 0
    assert metrics.net_pnl_usdt == pytest.approx(float(winner.net_pnl_usdt + loser.net_pnl_usdt))
