"""Versioned contracts and governance rules for dataset splits."""

from __future__ import annotations

import hashlib
import json
import tomllib
from dataclasses import asdict, dataclass
from decimal import Decimal
from enum import StrEnum
from pathlib import Path


class Partition(StrEnum):
    TRAIN = "TRAIN"
    PURGED_TRAIN_VALIDATION = "PURGED_TRAIN_VALIDATION"
    VALIDATION = "VALIDATION"
    EMBARGO_VALIDATION_TEST = "EMBARGO_VALIDATION_TEST"
    FINAL_HOLDOUT = "FINAL_HOLDOUT"


class FitPurpose(StrEnum):
    SCALER = "SCALER"
    SELECTOR = "SELECTOR"
    MODEL = "MODEL"
    CALIBRATOR = "CALIBRATOR"


@dataclass(frozen=True, slots=True)
class SplitConfig:
    version: str
    label_version: str
    base_interval_minutes: int
    prediction_horizon_minutes: int
    embargo_minutes: int
    validation_fraction: Decimal
    final_holdout_fraction: Decimal
    walk_forward_folds: int
    minimum_train_timestamps: int
    final_holdout_open_stage: str
    final_holdout_authorized_role: str

    def __post_init__(self) -> None:
        if self.version != "1.0.0" or self.label_version != "1.0.0":
            raise ValueError("unsupported split or label version")
        if self.base_interval_minutes <= 0 or self.prediction_horizon_minutes <= 0:
            raise ValueError("split intervals must be positive")
        if self.embargo_minutes < self.prediction_horizon_minutes:
            raise ValueError("embargo must be at least the prediction horizon")
        if self.prediction_horizon_minutes % self.base_interval_minutes:
            raise ValueError("horizon must align to the base interval")
        if not Decimal(0) < self.validation_fraction < Decimal("0.5"):
            raise ValueError("validation fraction must be between zero and one half")
        if not Decimal(0) < self.final_holdout_fraction < Decimal("0.5"):
            raise ValueError("holdout fraction must be between zero and one half")
        if self.walk_forward_folds < 2 or self.minimum_train_timestamps < 1:
            raise ValueError("walk-forward requires folds and a minimum train window")
        if self.final_holdout_open_stage != "W":
            raise ValueError("final holdout may first open only at Stage W")
        if self.final_holdout_authorized_role != "PROJECT_OWNER":
            raise ValueError("final holdout requires project-owner authorization")

    @classmethod
    def load(cls, path: Path) -> SplitConfig:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        data["validation_fraction"] = Decimal(data["validation_fraction"])
        data["final_holdout_fraction"] = Decimal(data["final_holdout_fraction"])
        return cls(**data)

    @property
    def canonical_hash(self) -> str:
        data = asdict(self)
        data["validation_fraction"] = str(self.validation_fraction)
        data["final_holdout_fraction"] = str(self.final_holdout_fraction)
        payload = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()

    @property
    def horizon_ms(self) -> int:
        return self.prediction_horizon_minutes * 60_000

    @property
    def embargo_gap_slots(self) -> int:
        return self.embargo_minutes // self.base_interval_minutes - 1


@dataclass(frozen=True, slots=True)
class SampleWindow:
    sample_id: str
    origin_sample_id: str
    symbol: str
    decision_time_ms: int
    vertical_barrier_time_ms: int


@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    fold: int
    train_ids: tuple[str, ...]
    purged_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]


def assert_fit_partition(purpose: FitPurpose, partition: Partition) -> None:
    """Prevent preprocessing/model fitting on selection or final-test samples."""

    allowed = {
        FitPurpose.SCALER: Partition.TRAIN,
        FitPurpose.SELECTOR: Partition.TRAIN,
        FitPurpose.MODEL: Partition.TRAIN,
        FitPurpose.CALIBRATOR: Partition.VALIDATION,
    }
    if partition is not allowed[purpose]:
        raise PermissionError(f"{purpose.value} cannot fit on {partition.value}")


def inherited_partition(origin_sample_id: str, assignments: dict[str, str]) -> Partition:
    """Force every augmentation/derived view to inherit its origin partition."""

    try:
        return Partition(assignments[origin_sample_id])
    except KeyError as error:
        raise KeyError("origin sample is absent from the locked split") from error
