"""Execution-aware, no-lookahead Stage J backtest engine."""

from ntnbinance.backtest.engine import simulate_trade
from ntnbinance.backtest.pipeline import BacktestPipeline, BacktestRunResult

__all__ = ["BacktestPipeline", "BacktestRunResult", "simulate_trade"]
