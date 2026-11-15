"""Locked feature-set configuration loader."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from ntnbinance.features.registry import FEATURE_VERSION


@dataclass(frozen=True, slots=True)
class CoverageConfig:
    basis_minimum_percent: float
    basis_minimum_span_days: int
    funding_minimum_percent: float
    funding_minimum_span_days: int
    open_interest_minimum_percent: float
    open_interest_minimum_span_days: int


@dataclass(frozen=True, slots=True)
class OptionalContextConfig:
    mark_index_basis: bool
    funding: bool
    open_interest: bool


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    version: str
    decision_rule: str
    minimum_15m_bars: int
    minimum_1h_bars: int
    atr_window: int
    short_volatility_window: int
    long_volatility_window: int
    volume_window: int
    coverage: CoverageConfig
    optional_context: OptionalContextConfig

    @classmethod
    def load(cls, path: Path) -> FeatureConfig:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        data["coverage"] = CoverageConfig(**data["coverage"])
        data["optional_context"] = OptionalContextConfig(**data["optional_context"])
        config = cls(**data)
        if config.version != FEATURE_VERSION:
            raise ValueError("unsupported feature version")
        if config.decision_rule != "event_time_ms < decision_time_ms":
            raise ValueError("point-in-time decision rule is immutable")
        if (
            config.minimum_15m_bars != 20
            or config.minimum_1h_bars != 4
            or config.atr_window != 14
            or config.short_volatility_window != 4
            or config.long_volatility_window != 16
            or config.volume_window != 20
        ):
            raise ValueError("feature windows differ from locked v2 registry")
        if not config.optional_context.mark_index_basis:
            raise ValueError("v2 requires audited mark/index basis")
        if config.optional_context.funding or config.optional_context.open_interest:
            raise ValueError("funding/OI are excluded until the minimum history span passes")
        return config
