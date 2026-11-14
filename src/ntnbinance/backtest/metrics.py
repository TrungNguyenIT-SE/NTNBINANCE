"""Portfolio and grouped metrics for execution-aware trade results."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Callable, Sequence

from ntnbinance.backtest.models import (
    BacktestConfig,
    ExitReason,
    FillStatus,
    PortfolioMetrics,
    TradeResult,
)


def summarize(
    results: Sequence[TradeResult], config: BacktestConfig, *, samples: int | None = None
) -> PortfolioMetrics:
    filled = [
        item
        for item in results
        if item.fill_status in {FillStatus.FILLED, FillStatus.PARTIALLY_FILLED}
    ]
    wins = [float(item.net_pnl_usdt) for item in filled if item.net_pnl_usdt > 0]
    losses = [float(item.net_pnl_usdt) for item in filled if item.net_pnl_usdt < 0]
    gross = sum(float(item.gross_pnl_usdt) for item in filled)
    net = sum(float(item.net_pnl_usdt) for item in filled)
    profit_factor = None if not losses else sum(wins) / abs(sum(losses))

    equity = float(config.starting_equity_usdt)
    peak = equity
    max_drawdown = 0.0
    for item in sorted(filled, key=lambda value: (value.exit_time_ms or 0, value.sample_id)):
        equity += float(item.net_pnl_usdt)
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, peak - equity)

    by_decision: dict[int, float] = defaultdict(float)
    for item in results:
        by_decision[item.decision_time_ms] += float(item.net_pnl_usdt) / float(
            config.starting_equity_usdt
        )
    period_returns = list(by_decision.values())
    sharpe: float | None = None
    sortino: float | None = None
    if len(period_returns) > 1:
        mean = sum(period_returns) / len(period_returns)
        variance = sum((value - mean) ** 2 for value in period_returns) / (len(period_returns) - 1)
        deviation = math.sqrt(variance)
        downside = math.sqrt(
            sum(min(value, 0.0) ** 2 for value in period_returns) / len(period_returns)
        )
        annualizer = math.sqrt(config.periods_per_year)
        sharpe = None if deviation == 0 else mean / deviation * annualizer
        sortino = None if downside == 0 else mean / downside * annualizer
    signal_count = sum(item.fill_status is not FillStatus.NO_TRADE for item in results)
    return PortfolioMetrics(
        samples=len(results) if samples is None else samples,
        signals=signal_count,
        filled_trades=len(filled),
        partial_fills=sum(item.fill_status is FillStatus.PARTIALLY_FILLED for item in results),
        unfilled=sum(item.fill_status is FillStatus.UNFILLED for item in results),
        gross_pnl_usdt=gross,
        net_pnl_usdt=net,
        spread_slippage_cost_usdt=sum(float(item.spread_slippage_cost_usdt) for item in filled),
        fee_cost_usdt=sum(float(item.fee_cost_usdt) for item in filled),
        funding_cost_usdt=sum(float(item.funding_cost_usdt) for item in filled),
        expectancy_usdt=0.0 if not filled else net / len(filled),
        profit_factor=profit_factor,
        maximum_drawdown_usdt=max_drawdown,
        maximum_drawdown_percent=max_drawdown / float(config.starting_equity_usdt),
        sharpe_annualized=sharpe,
        sortino_annualized=sortino,
        win_rate=0.0 if not filled else len(wins) / len(filled),
        take_profit_exits=sum(item.exit_reason is ExitReason.TAKE_PROFIT for item in filled),
        stop_loss_exits=sum(item.exit_reason is ExitReason.STOP_LOSS for item in filled),
        vertical_exits=sum(item.exit_reason is ExitReason.VERTICAL_BARRIER for item in filled),
    )


def grouped_metrics(
    results: Sequence[TradeResult],
    config: BacktestConfig,
    key: Callable[[TradeResult], str],
) -> dict[str, PortfolioMetrics]:
    groups: dict[str, list[TradeResult]] = defaultdict(list)
    for item in results:
        groups[key(item)].append(item)
    return {name: summarize(items, config) for name, items in sorted(groups.items())}
