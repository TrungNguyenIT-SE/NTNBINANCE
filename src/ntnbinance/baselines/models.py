"""Typed contracts for the Stage I baseline experiment."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

from ntnbinance.labels.models import Label, LabelReason
from ntnbinance.splits.models import Partition


@dataclass(frozen=True, slots=True)
class RuleConfig:
    minimum_atr_ratio: float
    maximum_atr_ratio: float
    trigger_atr_fraction: float


@dataclass(frozen=True, slots=True)
class LogisticConfig:
    C: float
    max_iter: int
    class_weight: str


@dataclass(frozen=True, slots=True)
class XGBoostConfig:
    n_estimators: int
    max_depth: int
    learning_rate: float
    subsample: float
    colsample_bytree: float
    n_jobs: int


@dataclass(frozen=True, slots=True)
class BaselineConfig:
    version: str
    seed: int
    class_order: tuple[str, ...]
    feature_version: str
    split_manifest: str
    label_run_id: str
    clean_run_id: str
    label_config: str
    rule: RuleConfig
    logistic_regression: LogisticConfig
    xgboost: XGBoostConfig

    @classmethod
    def load(cls, path: Path) -> BaselineConfig:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        data["class_order"] = tuple(data["class_order"])
        data["rule"] = RuleConfig(**data["rule"])
        data["logistic_regression"] = LogisticConfig(**data["logistic_regression"])
        data["xgboost"] = XGBoostConfig(**data["xgboost"])
        config = cls(**data)
        if config.version != "1.0.0" or config.feature_version != "1.0.0":
            raise ValueError("unsupported baseline or feature version")
        if config.class_order != tuple(label.value for label in Label):
            raise ValueError("class order must match the locked Label enum")
        if config.seed < 0 or config.logistic_regression.max_iter < 1:
            raise ValueError("invalid baseline seed or iteration count")
        if not 0 <= config.rule.minimum_atr_ratio < config.rule.maximum_atr_ratio:
            raise ValueError("invalid rule ATR range")
        return config

    @property
    def canonical_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class BaselineSample:
    sample_id: str
    partition: Partition
    symbol: str
    decision_time_ms: int
    vertical_barrier_time_ms: int
    label: Label
    reason: LabelReason
    reference_price: float
    upper_barrier: float
    lower_barrier: float
    barrier_time_ms: int | None
    execution_cost: float
    funding_cost: float
    vertical_close: float
    features: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class MetricSet:
    accuracy: float
    macro_f1: float
    macro_precision: float
    macro_recall: float
    per_class: dict[str, dict[str, float | int]]
    multiclass_brier: float
    ece_10_bin: float


@dataclass(frozen=True, slots=True)
class BacktestMetrics:
    samples: int
    trades: int
    trade_rate: float
    net_return_sum: float
    mean_return_per_sample: float
    mean_return_per_trade: float
    win_rate: float
    maximum_drawdown: float


FEATURE_NAMES = (
    "return_15m_1",
    "return_15m_4",
    "trend_1h_1",
    "trend_1h_3bar",
    "atr_ratio_14",
    "realized_volatility_4",
    "range_ratio_15m",
    "body_ratio_15m",
    "volume_ratio_4",
    "taker_buy_ratio",
    "mark_trade_basis",
    "index_trade_basis",
    "symbol_is_eth",
)
