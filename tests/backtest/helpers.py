from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from ntnbinance.backtest.models import (
    BacktestCase,
    BacktestConfig,
    InstrumentRules,
    MinuteCandle,
    Side,
)
from ntnbinance.labels.models import FundingEvent, VolatilityRegime


def config() -> BacktestConfig:
    base = BacktestConfig.load(Path("configs/backtest/backtest-v1.toml"))
    rules = InstrumentRules(
        price_tick_size=Decimal("0.1"),
        quantity_step_size=Decimal("0.1"),
        min_quantity=Decimal("0.1"),
        max_market_quantity=Decimal("100"),
        min_notional=Decimal("1"),
    )
    return replace(
        base,
        target_notional_usdt=Decimal("100"),
        taker_fee_rate_per_side=Decimal("0.001"),
        half_spread_bps_per_side=Decimal(0),
        slippage_bps_per_side=Decimal(0),
        max_candle_volume_participation=Decimal(1),
        instruments={"BTCUSDT": rules, "ETHUSDT": rules},
    )


def candle(
    minute: int,
    *,
    open_price: str = "100",
    high: str = "101",
    low: str = "99",
    close: str = "100",
    volume: str = "10",
) -> MinuteCandle:
    start = minute * 60_000
    return MinuteCandle(
        symbol="BTCUSDT",
        open_time_ms=start,
        close_time_ms=start + 59_999,
        open=Decimal(open_price),
        high=Decimal(high),
        low=Decimal(low),
        close=Decimal(close),
        volume_base=Decimal(volume),
    )


def case(
    candles: tuple[MinuteCandle, ...],
    *,
    side: Side = Side.LONG,
    funding: tuple[FundingEvent, ...] = (),
) -> BacktestCase:
    return BacktestCase(
        sample_id="sample",
        symbol="BTCUSDT",
        decision_time_ms=0,
        vertical_barrier_time_ms=3_600_000,
        reference_price=Decimal("100"),
        atr=Decimal("2"),
        regime=VolatilityRegime.NORMAL,
        prediction=side,
        confidence=Decimal("0.7"),
        candles=candles,
        funding_events=funding,
    )
