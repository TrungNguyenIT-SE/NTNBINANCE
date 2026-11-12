from __future__ import annotations

import json
from pathlib import Path

from ntnbinance.splits.pipeline import SplitPipeline

from .helpers import CONFIG_PATH, label_artifact


def test_manifest_is_locked_label_blind_and_idempotent(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifests" / "split-v1.json"
    pipeline = SplitPipeline(
        labels_root=label_artifact(tmp_path / "labels"),
        config_path=CONFIG_PATH,
        manifest_path=manifest_path,
    )
    first = pipeline.run()
    assert not first.reused
    assert first.counts == {
        "EMBARGO_VALIDATION_TEST": 6,
        "FINAL_HOLDOUT": 26,
        "PURGED_TRAIN_VALIDATION": 6,
        "TRAIN": 90,
        "VALIDATION": 26,
    }
    assert first.unique_timestamps == 77
    assert first.folds == 3
    assert len(first.manifest_sha256) == 64
    assert manifest_path.with_suffix(".sha256").is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["final_holdout"]["status"] == "SEALED"
    assert not data["final_holdout"]["opened"]
    assert "FINAL_HOLDOUT" not in data["development_distribution"]
    assert all("label" not in item for item in data["assignments"].values())

    second = pipeline.run()
    assert second.reused
    assert second.manifest_sha256 == first.manifest_sha256
