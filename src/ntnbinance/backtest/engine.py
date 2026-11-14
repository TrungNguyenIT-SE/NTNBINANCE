"""Conservative 1m event-driven fill and PnL simulation."""

from __future__ import annotations

from dataclasses import replace
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal

from ntnbinance.backtest.models import (
    BacktestCase,
    BacktestConfig,
    ExitReason,
    FillStatus,
    InstrumentRules,
    Side,
    TradeResult,
)

BPS = Decimal(10_000)
MINUTE_MS = 60_000


def _floor_step(value: Decimal, step: Decimal) -> Decimal:
    return (value / step).to_integral_value(rounding=ROUND_FLOOR) * step


def _price_tick(value: Decimal, tick: Decimal, *, round_up: bool) -> Decimal:
    rounding = ROUND_CEILING if round_up else ROUND_FLOOR
    return (value / tick).to_integral_value(rounding=rounding) * tick


def _eligible_open(timestamp_ms: int) -> int:
    return ((timestamp_ms + MINUTE_MS - 1) // MINUTE_MS) * MINUTE_MS


def _adverse_fill(
    raw_price: Decimal,
    *,
    is_buy: bool,
    config: BacktestConfig,
    rules: InstrumentRules,
    cost_multiplier: Decimal,
) -> Decimal:
    impact = (
        (config.half_spread_bps_per_side + config.slippage_bps_per_side) * cost_multiplier / BPS
    )
    adjusted = raw_price * (Decimal(1) + impact if is_buy else Decimal(1) - impact)
    return _price_tick(adjusted, rules.price_tick_size, round_up=is_buy)


def _empty_result(case: BacktestCase, arrival: int, status: FillStatus) -> TradeResult:
    return TradeResult(
        sample_id=case.sample_id,
        symbol=case.symbol,
        side=case.prediction,
        confidence=case.confidence,
        regime=case.regime,
        decision_time_ms=case.decision_time_ms,
        order_arrival_time_ms=arrival,
        entry_time_ms=None,
        exit_time_ms=None,
        fill_status=status,
        exit_reason=(ExitReason.ABSTAIN if status is FillStatus.NO_TRADE else ExitReason.NO_FILL),
        requested_quantity=Decimal(0),
        filled_quantity=Decimal(0),
        raw_entry_price=None,
        entry_fill_price=None,
        raw_exit_price=None,
        exit_fill_price=None,
        gross_pnl_usdt=Decimal(0),
        spread_slippage_cost_usdt=Decimal(0),
        fee_cost_usdt=Decimal(0),
        funding_cost_usdt=Decimal(0),
        net_pnl_usdt=Decimal(0),
        net_return_on_notional=Decimal(0),
        source_max_close_time_ms=None,
    )


def simulate_trade(
    case: BacktestCase,
    config: BacktestConfig,
    *,
    cost_multiplier: Decimal = Decimal(1),
    latency_ms: int | None = None,
) -> TradeResult:
    """Simulate one independent IOC market signal without using future data at entry."""

    actual_latency = config.latency_ms if latency_ms is None else latency_ms
    if actual_latency < 0 or cost_multiplier < 0:
        raise ValueError("latency and cost multiplier cannot be negative")
    arrival = case.decision_time_ms + actual_latency
    if case.prediction is Side.NO_TRADE:
        return _empty_result(case, arrival, FillStatus.NO_TRADE)
    rules = config.instruments[case.symbol]
    eligible_time = _eligible_open(arrival)
    entry_candle = next(
        (
            candle
            for candle in case.candles
            if candle.open_time_ms >= eligible_time
            and candle.open_time_ms < case.vertical_barrier_time_ms
        ),
        None,
    )
    if entry_candle is None:
        return _empty_result(case, arrival, FillStatus.UNFILLED)
    is_long = case.prediction is Side.LONG
    entry_fill = _adverse_fill(
        entry_candle.open,
        is_buy=is_long,
        config=config,
        rules=rules,
        cost_multiplier=cost_multiplier,
    )
    requested = min(
        _floor_step(config.target_notional_usdt / entry_fill, rules.quantity_step_size),
        rules.max_market_quantity,
    )
    if requested < rules.min_quantity or requested * entry_fill < rules.min_notional:
        return replace(
            _empty_result(case, arrival, FillStatus.UNFILLED),
            requested_quantity=requested,
        )
    available = _floor_step(
        entry_candle.volume_base * config.max_candle_volume_participation,
        rules.quantity_step_size,
    )
    filled = min(requested, available)
    if filled < rules.min_quantity or filled * entry_fill < rules.min_notional:
        return replace(
            _empty_result(case, arrival, FillStatus.UNFILLED),
            requested_quantity=requested,
        )
    status = FillStatus.FILLED if filled == requested else FillStatus.PARTIALLY_FILLED

    distance = case.atr * config.barrier_atr_multiplier
    if is_long:
        take = _price_tick(entry_fill + distance, rules.price_tick_size, round_up=False)
        stop = _price_tick(entry_fill - distance, rules.price_tick_size, round_up=True)
    else:
        take = _price_tick(entry_fill - distance, rules.price_tick_size, round_up=True)
        stop = _price_tick(entry_fill + distance, rules.price_tick_size, round_up=False)

    raw_exit: Decimal | None = None
    exit_time: int | None = None
    exit_reason = ExitReason.VERTICAL_BARRIER
    used_close_time = entry_candle.close_time_ms
    management = [
        candle
        for candle in case.candles
        if candle.open_time_ms >= entry_candle.open_time_ms
        and candle.close_time_ms < case.vertical_barrier_time_ms
    ]
    for candle in management:
        used_close_time = max(used_close_time, candle.close_time_ms)
        take_hit = candle.high >= take if is_long else candle.low <= take
        stop_hit = candle.low <= stop if is_long else candle.high >= stop
        if stop_hit:
            raw_exit = stop
            exit_time = candle.close_time_ms
            exit_reason = ExitReason.STOP_LOSS
            break
        if take_hit:
            raw_exit = take
            exit_time = candle.close_time_ms
            exit_reason = ExitReason.TAKE_PROFIT
            break
    if raw_exit is None:
        if not management:
            return replace(
                _empty_result(case, arrival, FillStatus.UNFILLED),
                requested_quantity=requested,
            )
        final = management[-1]
        raw_exit = final.close
        exit_time = final.close_time_ms
    assert exit_time is not None
    exit_fill = _adverse_fill(
        raw_exit,
        is_buy=not is_long,
        config=config,
        rules=rules,
        cost_multiplier=cost_multiplier,
    )
    direction = Decimal(1) if is_long else Decimal(-1)
    gross = direction * (raw_exit - entry_candle.open) * filled
    execution_price_pnl = direction * (exit_fill - entry_fill) * filled
    spread_slippage = gross - execution_price_pnl
    fee_rate = config.taker_fee_rate_per_side * cost_multiplier
    fees = (entry_fill + exit_fill) * filled * fee_rate
    funding_rate = sum(
        (
            event.funding_rate
            for event in case.funding_events
            if entry_candle.open_time_ms < event.funding_time_ms <= exit_time
        ),
        Decimal(0),
    )
    funding = direction * funding_rate * entry_fill * filled
    net = execution_price_pnl - fees - funding
    return TradeResult(
        sample_id=case.sample_id,
        symbol=case.symbol,
        side=case.prediction,
        confidence=case.confidence,
        regime=case.regime,
        decision_time_ms=case.decision_time_ms,
        order_arrival_time_ms=arrival,
        entry_time_ms=entry_candle.open_time_ms,
        exit_time_ms=exit_time,
        fill_status=status,
        exit_reason=exit_reason,
        requested_quantity=requested,
        filled_quantity=filled,
        raw_entry_price=entry_candle.open,
        entry_fill_price=entry_fill,
        raw_exit_price=raw_exit,
        exit_fill_price=exit_fill,
        gross_pnl_usdt=gross,
        spread_slippage_cost_usdt=spread_slippage,
        fee_cost_usdt=fees,
        funding_cost_usdt=funding,
        net_pnl_usdt=net,
        net_return_on_notional=net / (entry_fill * filled),
        source_max_close_time_ms=used_close_time,
    )
