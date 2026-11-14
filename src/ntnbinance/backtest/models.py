"""Typed Stage J configuration, market events and result contracts."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from ntnbinance.labels.models import FundingEvent, VolatilityRegime


class Side(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    NO_TRADE = "NO_TRADE"


class FillStatus(StrEnum):
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    UNFILLED = "UNFILLED"
    NO_TRADE = "NO_TRADE"


class ExitReason(StrEnum):
    TAKE_PROFIT = "TAKE_PROFIT"
    STOP_LOSS = "STOP_LOSS"
    VERTICAL_BARRIER = "VERTICAL_BARRIER"
    NO_FILL = "NO_FILL"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True, slots=True)
class InstrumentRules:
    price_tick_size: Decimal
    quantity_step_size: Decimal
    min_quantity: Decimal
    max_market_quantity: Decimal
    min_notional: Decimal

    def __post_init__(self) -> None:
        if any(value <= 0 for value in asdict(self).values()):
            raise ValueError("instrument rules must be positive")
        if self.min_quantity > self.max_market_quantity:
            raise ValueError("minimum quantity exceeds maximum market quantity")


@dataclass(frozen=True, slots=True)
class ExchangeSnapshot:
    endpoint: str
    observed_server_time_utc: str
    captured_client_date: str
    historical_at_decision_time: bool


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    version: str
    baseline_artifact: str
    split_manifest: str
    clean_run_id: str
    label_config: str
    exchange_snapshot_manifest: str
    starting_equity_usdt: Decimal
    target_notional_usdt: Decimal
    horizon_ms: int
    latency_ms: int
    taker_fee_rate_per_side: Decimal
    half_spread_bps_per_side: Decimal
    slippage_bps_per_side: Decimal
    max_candle_volume_participation: Decimal
    barrier_atr_multiplier: Decimal
    same_minute_policy: str
    partial_fill_policy: str
    cost_multipliers: tuple[Decimal, ...]
    latency_stress_ms: tuple[int, ...]
    confidence_edges: tuple[Decimal, ...]
    periods_per_year: int
    exchange_snapshot: ExchangeSnapshot
    instruments: dict[str, InstrumentRules]

    @classmethod
    def load(cls, path: Path) -> BacktestConfig:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        decimal_fields = {
            "starting_equity_usdt",
            "target_notional_usdt",
            "taker_fee_rate_per_side",
            "half_spread_bps_per_side",
            "slippage_bps_per_side",
            "max_candle_volume_participation",
            "barrier_atr_multiplier",
        }
        for field in decimal_fields:
            data[field] = Decimal(data[field])
        data["cost_multipliers"] = tuple(Decimal(value) for value in data["cost_multipliers"])
        data["latency_stress_ms"] = tuple(data["latency_stress_ms"])
        data["confidence_edges"] = tuple(Decimal(value) for value in data["confidence_edges"])
        data["exchange_snapshot"] = ExchangeSnapshot(**data["exchange_snapshot"])
        data["instruments"] = {
            symbol: InstrumentRules(**{name: Decimal(value) for name, value in rules.items()})
            for symbol, rules in data["instruments"].items()
        }
        config = cls(**data)
        config._validate()
        return config

    def _validate(self) -> None:
        if self.version != "1.0.0":
            raise ValueError("unsupported backtest config version")
        if self.same_minute_policy != "STOP_FIRST":
            raise ValueError("v1 requires conservative STOP_FIRST ambiguity handling")
        if self.partial_fill_policy != "IOC_CANCEL_REMAINDER":
            raise ValueError("v1 requires explicit IOC remainder cancellation")
        if self.horizon_ms <= 0 or self.latency_ms < 0 or self.periods_per_year <= 0:
            raise ValueError("invalid time or annualization config")
        if self.starting_equity_usdt <= 0 or self.target_notional_usdt <= 0:
            raise ValueError("equity and notional must be positive")
        if any(value < 0 for value in self.execution_decimals):
            raise ValueError("execution cost and participation values cannot be negative")
        if tuple(sorted(self.cost_multipliers)) != self.cost_multipliers:
            raise ValueError("cost multipliers must be ordered")
        if self.cost_multipliers[0] != Decimal(1):
            raise ValueError("cost stress must start at one")
        if self.latency_stress_ms[0] != self.latency_ms:
            raise ValueError("latency stress must start at base latency")
        if set(self.instruments) != {"BTCUSDT", "ETHUSDT"}:
            raise ValueError("backtest v1 instrument universe changed")
        if not self.exchange_snapshot_manifest.endswith(".json"):
            raise ValueError("exchange snapshot manifest must be JSON")
        if self.exchange_snapshot.historical_at_decision_time:
            raise ValueError("snapshot must not claim unavailable historical validity")

    @property
    def execution_decimals(self) -> tuple[Decimal, ...]:
        return (
            self.taker_fee_rate_per_side,
            self.half_spread_bps_per_side,
            self.slippage_bps_per_side,
            self.max_candle_volume_participation,
            self.barrier_atr_multiplier,
        )

    @property
    def canonical_hash(self) -> str:
        data = asdict(self)

        def normalize(value: object) -> object:
            if isinstance(value, Decimal):
                return str(value)
            if isinstance(value, dict):
                return {key: normalize(item) for key, item in sorted(value.items())}
            if isinstance(value, (tuple, list)):
                return [normalize(item) for item in value]
            return value

        return hashlib.sha256(
            json.dumps(normalize(data), separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class MinuteCandle:
    symbol: str
    open_time_ms: int
    close_time_ms: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume_base: Decimal


@dataclass(frozen=True, slots=True)
class BacktestCase:
    sample_id: str
    symbol: str
    decision_time_ms: int
    vertical_barrier_time_ms: int
    reference_price: Decimal
    atr: Decimal
    regime: VolatilityRegime
    prediction: Side
    confidence: Decimal
    candles: tuple[MinuteCandle, ...]
    funding_events: tuple[FundingEvent, ...]


@dataclass(frozen=True, slots=True)
class BacktestInput:
    sample_id: str
    symbol: str
    decision_time_ms: int
    vertical_barrier_time_ms: int
    reference_price: Decimal
    atr: Decimal
    regime: VolatilityRegime
    features: tuple[float, ...]
    candles: tuple[MinuteCandle, ...]
    funding_events: tuple[FundingEvent, ...]


@dataclass(frozen=True, slots=True)
class TradeResult:
    sample_id: str
    symbol: str
    side: Side
    confidence: Decimal
    regime: VolatilityRegime
    decision_time_ms: int
    order_arrival_time_ms: int
    entry_time_ms: int | None
    exit_time_ms: int | None
    fill_status: FillStatus
    exit_reason: ExitReason
    requested_quantity: Decimal
    filled_quantity: Decimal
    raw_entry_price: Decimal | None
    entry_fill_price: Decimal | None
    raw_exit_price: Decimal | None
    exit_fill_price: Decimal | None
    gross_pnl_usdt: Decimal
    spread_slippage_cost_usdt: Decimal
    fee_cost_usdt: Decimal
    funding_cost_usdt: Decimal
    net_pnl_usdt: Decimal
    net_return_on_notional: Decimal
    source_max_close_time_ms: int | None


@dataclass(frozen=True, slots=True)
class PortfolioMetrics:
    samples: int
    signals: int
    filled_trades: int
    partial_fills: int
    unfilled: int
    gross_pnl_usdt: float
    net_pnl_usdt: float
    spread_slippage_cost_usdt: float
    fee_cost_usdt: float
    funding_cost_usdt: float
    expectancy_usdt: float
    profit_factor: float | None
    maximum_drawdown_usdt: float
    maximum_drawdown_percent: float
    sharpe_annualized: float | None
    sortino_annualized: float | None
    win_rate: float
    take_profit_exits: int
    stop_loss_exits: int
    vertical_exits: int
