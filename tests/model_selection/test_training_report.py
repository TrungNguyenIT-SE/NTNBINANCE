from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

from ntnbinance.model_selection.models import ModelSelectionConfig
from ntnbinance.model_selection.pipeline import (
    ModelSelectionPipeline,
    _aligned_probabilities,
    _candidate_family,
    _family_sensitivity_models,
    _markdown_report,
    _matrix_family,
    _models,
    _sha256,
    _tune_xgboost,
    _validation_tune_xgboost,
)

CONFIG_PATH = Path("configs/models/model-selection-v1.toml")
ARTIFACT_PATH = Path("models/candidates/model-selection-v1.json")


def _small_config() -> ModelSelectionConfig:
    config = ModelSelectionConfig.load(CONFIG_PATH)
    sensitivity = replace(
        config.sensitivity,
        depths=(1,),
        estimators=(2,),
        learning_rates=(0.1,),
        time_series_splits=2,
        gap_samples=0,
        svc_cs=(1.0,),
        svc_gammas=("scale",),
        tree_depths=(2,),
        tree_min_samples_leaf=(1,),
        tree_estimators=2,
    )
    return replace(
        config,
        image=replace(config.image, pca_components=3),
        xgboost=replace(config.xgboost, n_estimators=2, max_depth=1),
        sensitivity=sensitivity,
    )


def test_candidate_builders_and_bounded_tuners() -> None:
    config = _small_config()
    rng = np.random.default_rng(config.seed)
    y_train = np.tile(np.arange(3, dtype=np.int64), 8)
    numeric = rng.normal(size=(24, 4))
    image = rng.normal(size=(24, 8))
    fusion = np.hstack((numeric, image))

    candidates = _models(config, numeric_count=4)
    assert set(candidates) == {
        "numeric_logistic",
        "numeric_xgboost",
        "image_logistic",
        "fusion_logistic",
        "fusion_xgboost",
    }
    for name, model in candidates.items():
        matrix = (
            image
            if name.startswith("image_")
            else fusion
            if name.startswith("fusion_")
            else numeric
        )
        model.fit(matrix, y_train)
        assert model.predict_proba(matrix[:2]).shape == (2, 3)

    sensitivity = _family_sensitivity_models(config)
    assert len(sensitivity) == 6
    assert any("svc" in name for name in sensitivity)
    assert any("random_forest" in name for name in sensitivity)
    assert any("extra_trees" in name for name in sensitivity)

    selected, scores, parameters = _tune_xgboost(numeric, y_train, config)
    assert len(scores) == 1
    assert parameters == {"max_depth": 1, "n_estimators": 2, "learning_rate": 0.1}
    selected.fit(numeric, y_train)

    validation_model, validation_scores, validation_parameters = _validation_tune_xgboost(
        numeric[:18],
        y_train[:18],
        numeric[18:],
        y_train[18:],
        config,
    )
    assert validation_model.predict_proba(numeric[18:]).shape == (6, 3)
    assert len(validation_scores) == 1
    assert validation_parameters == parameters


def test_alignment_family_routing_and_hash(tmp_path: Path) -> None:
    raw = np.asarray([[0.7, 0.3]], dtype=np.float64)
    aligned = _aligned_probabilities(raw, np.asarray([2, 0], dtype=np.int64), 3)
    assert aligned.tolist() == [[0.3, 0.0, 0.7]]
    assert _candidate_family("numeric_logistic") == "numeric"
    assert _candidate_family("image_logistic") == "image"
    assert _candidate_family("fusion_logistic") == "fusion"
    assert _matrix_family("numeric_v1_xgboost") == "numeric_v1"
    assert _matrix_family("numeric_xgboost") == "numeric"
    target = tmp_path / "content.txt"
    target.write_text("locked", encoding="utf-8")
    assert len(_sha256(target)) == 64


def test_report_and_atomic_publication_cover_no_go_contract(tmp_path: Path) -> None:
    artifact = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    report = _markdown_report(artifact)
    assert "Result: **NO-GO**" in report
    assert "Stage P must not begin" in report
    assert "New cash cost is **0 VNĐ**" in report

    artifact_dir = tmp_path / "models"
    report_path = tmp_path / "reports" / "selection.md"
    pipeline = ModelSelectionPipeline(
        project_root=tmp_path,
        config_path=CONFIG_PATH,
        labels_path=tmp_path / "labels.jsonl",
        clean_root=tmp_path / "clean",
        artifact_dir=artifact_dir,
        report_path=report_path,
    )
    pipeline._publish(artifact, {"fitted": True})
    published = json.loads((artifact_dir / "model-selection-v1.json").read_text(encoding="utf-8"))
    assert published["champion_artifact"]["sha256"]
    assert (artifact_dir / "champion-v1.joblib").is_file()
    assert report_path.is_file()

    pipeline._publish(artifact, None)
    published = json.loads((artifact_dir / "model-selection-v1.json").read_text(encoding="utf-8"))
    assert published["champion_artifact"] is None
    assert not (artifact_dir / "champion-v1.joblib").exists()
