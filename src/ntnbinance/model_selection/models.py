"""Typed Stage O configuration and experiment contracts."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path

from ntnbinance.baselines.models import BaselineSample
from ntnbinance.features.registry import FEATURE_VERSION
from ntnbinance.labels.models import Label


@dataclass(frozen=True, slots=True)
class ImageConfig:
    width: int
    height: int
    embedding_width: int
    embedding_height: int
    pca_components: int
    theme: str


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
class SensitivityConfig:
    depths: tuple[int, ...]
    estimators: tuple[int, ...]
    learning_rates: tuple[float, ...]
    time_series_splits: int
    gap_samples: int
    svc_cs: tuple[float, ...]
    svc_gammas: tuple[str, ...]
    tree_depths: tuple[int, ...]
    tree_min_samples_leaf: tuple[int, ...]
    tree_estimators: int


@dataclass(frozen=True, slots=True)
class ResourceConfig:
    maximum_prediction_latency_ms: float
    maximum_python_peak_memory_mb: float
    maximum_artifact_bytes: int


@dataclass(frozen=True, slots=True)
class ModelSelectionConfig:
    version: str
    seed: int
    feature_version: str
    image_pipeline_version: str
    class_order: tuple[str, ...]
    split_manifest: str
    label_run_id: str
    clean_run_id: str
    label_config: str
    baseline_macro_f1: float
    minimum_macro_f1_gain: float
    minimum_vision_macro_f1_gain: float
    image: ImageConfig
    logistic: LogisticConfig
    xgboost: XGBoostConfig
    sensitivity: SensitivityConfig
    resources: ResourceConfig

    @classmethod
    def load(cls, path: Path) -> ModelSelectionConfig:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
        raw["class_order"] = tuple(raw["class_order"])
        raw["image"] = ImageConfig(**raw["image"])
        raw["logistic"] = LogisticConfig(**raw["logistic"])
        raw["xgboost"] = XGBoostConfig(**raw["xgboost"])
        sensitivity = raw["sensitivity"]
        for key in (
            "depths",
            "estimators",
            "learning_rates",
            "svc_cs",
            "svc_gammas",
            "tree_depths",
            "tree_min_samples_leaf",
        ):
            sensitivity[key] = tuple(sensitivity[key])
        raw["sensitivity"] = SensitivityConfig(**sensitivity)
        raw["resources"] = ResourceConfig(**raw["resources"])
        config = cls(**raw)
        if config.version != "1.0.0" or config.feature_version != FEATURE_VERSION:
            raise ValueError("unsupported model-selection or feature version")
        if config.class_order != tuple(label.value for label in Label):
            raise ValueError("class order differs from locked label enum")
        if config.seed < 0 or config.logistic.max_iter < 1 or config.xgboost.n_jobs != 1:
            raise ValueError("invalid deterministic training configuration")
        if config.image.width < 800 or config.image.height < 600:
            raise ValueError("image benchmark is below the Stage K contract")
        if not 0 < config.minimum_macro_f1_gain < 1:
            raise ValueError("invalid meaningful-improvement threshold")
        if (
            not config.sensitivity.depths
            or not config.sensitivity.estimators
            or not config.sensitivity.learning_rates
            or config.sensitivity.time_series_splits < 2
            or config.sensitivity.gap_samples < 0
            or config.sensitivity.tree_estimators < 1
        ):
            raise ValueError("invalid sensitivity grid")
        return config

    @property
    def canonical_hash(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class ModelSample:
    baseline: BaselineSample
    numeric_features: tuple[float, ...]
    image_features: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class LoadedModelSamples:
    samples: tuple[ModelSample, ...]
    sealed_holdout_rows: int
    image_encoding_ms: float
    rejected_train_missing_features: int
    rejected_validation_missing_features: int


@dataclass(frozen=True, slots=True)
class SelectionRunResult:
    run_id: str
    champion: str
    artifact_path: Path
    report_path: Path
    sealed_holdout_rows: int
