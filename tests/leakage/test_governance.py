from __future__ import annotations

import json
from pathlib import Path

import pytest

from ntnbinance.splits.guard import require_holdout_unlock
from ntnbinance.splits.models import (
    FitPurpose,
    Partition,
    assert_fit_partition,
    inherited_partition,
)


def test_fit_scopes_are_fail_closed() -> None:
    assert_fit_partition(FitPurpose.SCALER, Partition.TRAIN)
    assert_fit_partition(FitPurpose.SELECTOR, Partition.TRAIN)
    assert_fit_partition(FitPurpose.MODEL, Partition.TRAIN)
    assert_fit_partition(FitPurpose.CALIBRATOR, Partition.VALIDATION)
    with pytest.raises(PermissionError, match="cannot fit"):
        assert_fit_partition(FitPurpose.SCALER, Partition.VALIDATION)
    with pytest.raises(PermissionError, match="cannot fit"):
        assert_fit_partition(FitPurpose.CALIBRATOR, Partition.FINAL_HOLDOUT)


def test_augmentation_inherits_origin_partition() -> None:
    assignments = {"origin": "TRAIN", "held-out": "FINAL_HOLDOUT"}
    assert inherited_partition("origin", assignments) is Partition.TRAIN
    assert inherited_partition("held-out", assignments) is Partition.FINAL_HOLDOUT
    with pytest.raises(KeyError, match="absent"):
        inherited_partition("synthetic-without-origin", assignments)


def test_final_holdout_requires_complete_stage_w_unlock(tmp_path: Path) -> None:
    unlock = tmp_path / "unlock.json"
    with pytest.raises(PermissionError, match="sealed"):
        require_holdout_unlock(unlock)
    invalid = {
        "authorized_role": "PROJECT_OWNER",
        "decision": "OPEN_FINAL_HOLDOUT_ONCE",
        "locked_artifacts": {},
        "opened_at_utc": "2026-11-13T00:00:00Z",
        "stage": "W",
    }
    unlock.write_text(json.dumps(invalid), encoding="utf-8")
    with pytest.raises(PermissionError, match="all pipeline artifacts"):
        require_holdout_unlock(unlock)
    invalid["locked_artifacts"] = {
        "feature_hash": "feature1",
        "model_hash": "model123",
        "calibration_hash": "calib123",
        "risk_policy_hash": "risk123",
        "code_commit": "commit1",
    }
    unlock.write_text(json.dumps(invalid), encoding="utf-8")
    result = require_holdout_unlock(unlock)
    assert result["decision"] == "OPEN_FINAL_HOLDOUT_ONCE"


def test_malformed_holdout_unlock_variants_fail_closed(tmp_path: Path) -> None:
    unlock = tmp_path / "unlock.json"
    unlock.write_text("[]", encoding="utf-8")
    with pytest.raises(PermissionError, match="invalid"):
        require_holdout_unlock(unlock)

    locked_artifacts: dict[str, str] = {
        "feature_hash": "feature1",
        "model_hash": "model123",
        "calibration_hash": "calib123",
        "risk_policy_hash": "risk123",
        "code_commit": "commit1",
    }
    base: dict[str, object] = {
        "authorized_role": "PROJECT_OWNER",
        "decision": "OPEN_FINAL_HOLDOUT_ONCE",
        "locked_artifacts": locked_artifacts,
        "opened_at_utc": "2026-11-13T00:00:00Z",
        "stage": "W",
    }
    variants = (
        ({**base, "stage": "V"}, "authorization"),
        ({**base, "decision": "PEEK"}, "decision"),
        ({**base, "opened_at_utc": "2026-11-13"}, "timestamp"),
        (
            {
                **base,
                "locked_artifacts": {**locked_artifacts, "model_hash": "bad"},
            },
            "hashes",
        ),
    )
    for payload, message in variants:
        unlock.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(PermissionError, match=message):
            require_holdout_unlock(unlock)
