"""Deterministic triple-barrier label engine with explicit net costs."""

from __future__ import annotations

from decimal import Decimal

from ntnbinance.data_quality.models import CandleRecord
from ntnbinance.labels.models import (
    FundingEvent,
    Label,
    LabelConfig,
    LabelReason,
    LabelResult,
    VolatilityRegime,
    candle_quality_passes,
)


def true_range(current: CandleRecord, previous_close: Decimal) -> Decimal:
    return max(
        current.high - current.low,
        abs(current.high - previous_close),
        abs(current.low - previous_close),
    )


def calculate_atr(history: list[CandleRecord], window: int) -> Decimal:
    """Calculate simple ATR from exactly ``window`` point-in-time true ranges."""

    if len(history) != window + 1:
        raise ValueError("ATR history must contain window + 1 candles")
    ranges = [
        true_range(history[index], history[index - 1].close) for index in range(1, len(history))
    ]
    return sum(ranges, Decimal(0)) / Decimal(window)


def _regime(atr: Decimal, reference: Decimal, config: LabelConfig) -> VolatilityRegime:
    ratio = atr / reference
    if ratio < config.low_volatility_atr_ratio:
        return VolatilityRegime.LOW
    if ratio < config.high_volatility_atr_ratio:
        return VolatilityRegime.NORMAL
    return VolatilityRegime.HIGH


def _first_touch(
    future: list[CandleRecord],
    intrabars: list[CandleRecord],
    upper: Decimal,
    lower: Decimal,
) -> tuple[Label | None, int | None, bool]:
    """Resolve first touch with 1m evidence; never infer path inside one OHLC bar."""

    future_start = future[0].open_time_ms
    future_end = future[-1].close_time_ms
    relevant = [
        record
        for record in intrabars
        if future_start <= record.open_time_ms and record.close_time_ms <= future_end
    ]
    for record in relevant:
        upper_hit = record.high >= upper
        lower_hit = record.low <= lower
        if upper_hit and lower_hit:
            return None, record.close_time_ms, True
        if upper_hit:
            return Label.LONG, record.close_time_ms, False
        if lower_hit:
            return Label.SHORT, record.close_time_ms, False
    # A 15m touch without complete 1m evidence is deliberately ambiguous.
    if any(record.high >= upper or record.low <= lower for record in future):
        return None, None, True
    return None, None, False


def _funding_cost(
    direction: Label,
    events: list[FundingEvent],
    symbol: str,
    decision_time_ms: int,
    exit_time_ms: int,
) -> Decimal:
    rates = sum(
        (
            event.funding_rate
            for event in events
            if event.symbol == symbol and decision_time_ms < event.funding_time_ms <= exit_time_ms
        ),
        Decimal(0),
    )
    return rates if direction is Label.LONG else -rates


def label_sample(
    *,
    history: list[CandleRecord],
    future: list[CandleRecord],
    intrabars: list[CandleRecord],
    funding_events: list[FundingEvent],
    config: LabelConfig,
) -> LabelResult:
    """Label one decision using no candle after the configured vertical barrier."""

    if len(history) != config.atr_window + 1:
        raise ValueError("history length does not match ATR config")
    if len(future) != config.horizon_bars:
        raise ValueError("future length does not match vertical barrier")
    decision = history[-1]
    expected_step = 900_000
    if any(
        record.symbol != decision.symbol
        or record.dataset != config.price_dataset
        or record.interval != config.interval
        for record in history + future
    ):
        raise ValueError("label sample must contain one symbol of 15m candles")
    expected_history = [
        decision.open_time_ms - expected_step * index for index in range(config.atr_window, -1, -1)
    ]
    if [record.open_time_ms for record in history] != expected_history:
        raise ValueError("ATR history must be contiguous and chronological")
    expected_future = [
        decision.open_time_ms + expected_step * index for index in range(1, config.horizon_bars + 1)
    ]
    if [record.open_time_ms for record in future] != expected_future:
        raise ValueError("future candles must be four contiguous bars")

    atr = calculate_atr(history, config.atr_window)
    reference = decision.close
    distance = atr * config.barrier_atr_multiplier
    upper = reference + distance
    lower = reference - distance
    decision_time = decision.close_time_ms + 1
    entry_time = decision_time + config.latency_ms
    vertical_time = future[-1].close_time_ms + 1
    relevant_intrabars = [
        record
        for record in intrabars
        if record.symbol == decision.symbol
        and record.dataset == config.price_dataset
        and record.interval == config.intrabar_interval
        and future[0].open_time_ms <= record.open_time_ms
        and record.close_time_ms <= future[-1].close_time_ms
    ]
    relevant_intrabars.sort(key=lambda record: record.open_time_ms)
    expected_intrabar_times = list(
        range(future[0].open_time_ms, future[-1].close_time_ms + 1, 60_000)
    )
    intrabars_complete = [
        record.open_time_ms for record in relevant_intrabars
    ] == expected_intrabar_times
    relevant_funding = [
        event
        for event in funding_events
        if event.symbol == decision.symbol and entry_time < event.funding_time_ms <= vertical_time
    ]
    source_identities = tuple(
        [record.raw_identity for record in history + future + relevant_intrabars]
        + [event.raw_identity for event in relevant_funding]
    )

    def build_result(
        *,
        label: Label,
        reason: LabelReason,
        barrier_time_ms: int | None,
        gross_return: Decimal = Decimal(0),
        execution_cost: Decimal = Decimal(0),
        funding_cost: Decimal = Decimal(0),
        net_return: Decimal = Decimal(0),
    ) -> LabelResult:
        return LabelResult(
            config_version=config.version,
            config_hash=config.canonical_hash,
            symbol=decision.symbol,
            decision_time_ms=decision_time,
            entry_time_ms=entry_time,
            vertical_barrier_time_ms=vertical_time,
            label=label,
            reason=reason,
            reference_price=reference,
            atr=atr,
            upper_barrier=upper,
            lower_barrier=lower,
            barrier_time_ms=barrier_time_ms,
            gross_return=gross_return,
            execution_cost=execution_cost,
            funding_cost=funding_cost,
            net_return=net_return,
            volatility_regime=_regime(atr, reference, config),
            source_identities=source_identities,
        )

    if not intrabars_complete or not all(
        candle_quality_passes(record, config) for record in history + future + relevant_intrabars
    ):
        return build_result(
            label=Label.NO_TRADE,
            reason=LabelReason.DATA_QUALITY,
            barrier_time_ms=None,
            gross_return=Decimal(0),
            execution_cost=Decimal(0),
            funding_cost=Decimal(0),
            net_return=Decimal(0),
        )

    direction, barrier_time, ambiguous = _first_touch(future, relevant_intrabars, upper, lower)
    if ambiguous:
        return build_result(
            label=Label.NO_TRADE,
            reason=LabelReason.AMBIGUOUS_INTRABAR,
            barrier_time_ms=barrier_time,
            gross_return=Decimal(0),
            execution_cost=Decimal(0),
            funding_cost=Decimal(0),
            net_return=Decimal(0),
        )
    if direction is None or barrier_time is None:
        return build_result(
            label=Label.NO_TRADE,
            reason=LabelReason.VERTICAL_BARRIER,
            barrier_time_ms=None,
            gross_return=Decimal(0),
            execution_cost=Decimal(0),
            funding_cost=Decimal(0),
            net_return=Decimal(0),
        )

    gross = distance / reference
    execution = config.fixed_execution_cost
    funding = _funding_cost(direction, funding_events, decision.symbol, entry_time, barrier_time)
    net = gross - execution - funding
    if net <= config.minimum_net_return:
        label = Label.NO_TRADE
        reason = LabelReason.COST_REMOVED_EDGE
    else:
        label = direction
        reason = (
            LabelReason.UPPER_BARRIER_NET_POSITIVE
            if direction is Label.LONG
            else LabelReason.LOWER_BARRIER_NET_POSITIVE
        )
    return build_result(
        label=label,
        reason=reason,
        barrier_time_ms=barrier_time,
        gross_return=gross,
        execution_cost=execution,
        funding_cost=funding,
        net_return=net,
    )
