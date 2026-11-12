"""Typed and validated Stage G label contracts."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

from ntnbinance.data_contract import QualityFlag
from ntnbinance.data_quality.models import CandleRecord


class Label(StrEnum):
    LONG = "LONG"
    SHORT = "SHORT"
    NO_TRADE = "NO_TRADE"


class LabelReason(StrEnum):
    UPPER_BARRIER_NET_POSITIVE = "UPPER_BARRIER_NET_POSITIVE"
    LOWER_BARRIER_NET_POSITIVE = "LOWER_BARRIER_NET_POSITIVE"
    COST_REMOVED_EDGE = "COST_REMOVED_EDGE"
    VERTICAL_BARRIER = "VERTICAL_BARRIER"
    AMBIGUOUS_INTRABAR = "AMBIGUOUS_INTRABAR"
    DATA_QUALITY = "DATA_QUALITY"


class VolatilityRegime(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"


@dataclass(frozen=True, slots=True)
class LabelConfig:
    version: str
    price_dataset: str
    interval: str
    intrabar_interval: str
    atr_window: int
    atr_method: str
    barrier_atr_multiplier: Decimal
    horizon_bars: int
    secondary_horizons: tuple[int, ...]
    minimum_net_return: Decimal
    taker_fee_rate_per_side: Decimal
    half_spread_bps_per_side: Decimal
    slippage_bps_per_side: Decimal
    latency_bps_entry: Decimal
    latency_ms: int
    same_intrabar_policy: str
    low_volatility_atr_ratio: Decimal
    high_volatility_atr_ratio: Decimal
    disallowed_quality_flags: frozenset[QualityFlag]

    def __post_init__(self) -> None:
        if self.version != "1.0.0":
            raise ValueError("unsupported label config version")
        if self.price_dataset != "trade_klines" or self.interval != "15m":
            raise ValueError("label v1 requires 15m trade klines")
        if self.intrabar_interval != "1m" or self.atr_method != "simple_true_range":
            raise ValueError("label v1 requires 1m intrabars and simple true range")
        if self.atr_window < 2 or self.horizon_bars < 1:
            raise ValueError("ATR window and horizon must be positive")
        decimals = (
            self.barrier_atr_multiplier,
            self.minimum_net_return,
            self.taker_fee_rate_per_side,
            self.half_spread_bps_per_side,
            self.slippage_bps_per_side,
            self.latency_bps_entry,
            self.low_volatility_atr_ratio,
            self.high_volatility_atr_ratio,
        )
        if any(value < 0 for value in decimals):
            raise ValueError("label config costs and thresholds cannot be negative")
        if self.barrier_atr_multiplier == 0 or self.latency_ms < 0:
            raise ValueError("barrier multiplier must be positive and latency non-negative")
        if self.low_volatility_atr_ratio >= self.high_volatility_atr_ratio:
            raise ValueError("volatility regime thresholds are invalid")
        if self.same_intrabar_policy != "NO_TRADE":
            raise ValueError("label v1 fail-safe intrabar policy must be NO_TRADE")

    @classmethod
    def load(cls, path: Path) -> LabelConfig:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        decimal_fields = {
            "barrier_atr_multiplier",
            "minimum_net_return",
            "taker_fee_rate_per_side",
            "half_spread_bps_per_side",
            "slippage_bps_per_side",
            "latency_bps_entry",
            "low_volatility_atr_ratio",
            "high_volatility_atr_ratio",
        }
        for field in decimal_fields:
            data[field] = Decimal(data[field])
        data["secondary_horizons"] = tuple(data["secondary_horizons"])
        data["disallowed_quality_flags"] = frozenset(
            QualityFlag(value) for value in data["disallowed_quality_flags"]
        )
        return cls(**data)

    @property
    def canonical_hash(self) -> str:
        data = asdict(self)
        for key, value in tuple(data.items()):
            if isinstance(value, Decimal):
                data[key] = str(value)
            elif isinstance(value, (set, frozenset)):
                data[key] = sorted(str(item) for item in value)
        encoded = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()

    @property
    def fixed_execution_cost(self) -> Decimal:
        bps = Decimal("10000")
        return (
            self.taker_fee_rate_per_side * 2
            + self.half_spread_bps_per_side * 2 / bps
            + self.slippage_bps_per_side * 2 / bps
            + self.latency_bps_entry / bps
        )


@dataclass(frozen=True, slots=True)
class FundingEvent:
    symbol: str
    funding_time_ms: int
    funding_rate: Decimal
    raw_identity: str


@dataclass(frozen=True, slots=True)
class LabelResult:
    config_version: str
    config_hash: str
    symbol: str
    decision_time_ms: int
    entry_time_ms: int
    vertical_barrier_time_ms: int
    label: Label
    reason: LabelReason
    reference_price: Decimal
    atr: Decimal
    upper_barrier: Decimal
    lower_barrier: Decimal
    barrier_time_ms: int | None
    gross_return: Decimal
    execution_cost: Decimal
    funding_cost: Decimal
    net_return: Decimal
    volatility_regime: VolatilityRegime
    source_identities: tuple[str, ...]


def candle_quality_passes(record: CandleRecord, config: LabelConfig) -> bool:
    return record.is_closed and not (set(record.quality_flags) & config.disallowed_quality_flags)
