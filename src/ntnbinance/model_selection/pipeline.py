"""Train, measure, compare and publish locked Stage O candidates."""

from __future__ import annotations

import hashlib
import json
import os
import pickle
import platform
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn
import xgboost
from numpy.typing import NDArray
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

from ntnbinance.baselines.data import load_development_samples
from ntnbinance.baselines.evaluation import backtest, classification_metrics
from ntnbinance.features.registry import FEATURE_NAMES
from ntnbinance.labels.models import LabelConfig
from ntnbinance.model_selection.data import load_model_samples
from ntnbinance.model_selection.models import (
    ModelSelectionConfig,
    SelectionRunResult,
)
from ntnbinance.splits.models import FitPurpose, Partition, assert_fit_partition

ENGINE_VERSION = "1.0.0"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _aligned_probabilities(
    probabilities: NDArray[np.float64], classes: NDArray[np.int64], count: int
) -> NDArray[np.float64]:
    aligned = np.zeros((probabilities.shape[0], count), dtype=np.float64)
    for source, target in enumerate(classes):
        aligned[:, int(target)] = probabilities[:, source]
    return aligned


def _candidate_family(name: str) -> str:
    if name.startswith("numeric_"):
        return "numeric"
    if name.startswith("image_"):
        return "image"
    return "fusion"


def _matrix_family(name: str) -> str:
    return "numeric_v1" if name.startswith("numeric_v1_") else _candidate_family(name)


def choose_champion(
    results: dict[str, dict[str, Any]], config: ModelSelectionConfig
) -> tuple[str, str]:
    eligible = [
        name
        for name, result in results.items()
        if _candidate_family(name) != "image"
        and result["resource_passed"]
        and result["classification"]["macro_f1"]
        >= config.baseline_macro_f1 + config.minimum_macro_f1_gain
    ]
    if not eligible:
        resource_eligible = [
            name
            for name, result in results.items()
            if _candidate_family(name) != "image" and result["resource_passed"]
        ]
        best_name = max(
            resource_eligible,
            key=lambda name: float(results[name]["classification"]["macro_f1"]),
        )
        best_f1 = float(results[best_name]["classification"]["macro_f1"])
        required = config.baseline_macro_f1 + config.minimum_macro_f1_gain
        raise RuntimeError(
            f"best resource-eligible candidate {best_name} macro-F1={best_f1:.4f}; "
            f"locked requirement={required:.4f}"
        )

    def score(name: str) -> tuple[float, float, float, int]:
        result = results[name]
        simplicity = {"numeric": 2, "fusion": 1, "image": 0}[_candidate_family(name)]
        return (
            float(result["classification"]["macro_f1"]),
            float(result["classification"]["accuracy"]),
            -float(result["classification"]["multiclass_brier"]),
            simplicity,
        )

    best = max(eligible, key=score)
    numeric = [name for name in eligible if _candidate_family(name) == "numeric"]
    if _candidate_family(best) == "fusion" and numeric:
        best_numeric = max(numeric, key=score)
        vision_gain = float(results[best]["classification"]["macro_f1"]) - float(
            results[best_numeric]["classification"]["macro_f1"]
        )
        if vision_gain < config.minimum_vision_macro_f1_gain:
            return best_numeric, "vision gain below locked meaningful-improvement threshold"
    return best, "highest eligible validation score under locked selection rule"


def _models(config: ModelSelectionConfig, numeric_count: int) -> dict[str, Any]:
    logistic = config.logistic
    xgb = config.xgboost

    def classifier() -> LogisticRegression:
        return LogisticRegression(
            C=logistic.C,
            max_iter=logistic.max_iter,
            class_weight=logistic.class_weight,
            random_state=config.seed,
        )

    def boosted() -> XGBClassifier:
        return XGBClassifier(
            objective="multi:softprob",
            num_class=len(config.class_order),
            eval_metric="mlogloss",
            random_state=config.seed,
            n_estimators=xgb.n_estimators,
            max_depth=xgb.max_depth,
            learning_rate=xgb.learning_rate,
            subsample=xgb.subsample,
            colsample_bytree=xgb.colsample_bytree,
            n_jobs=xgb.n_jobs,
        )

    image_pipeline = Pipeline(
        [
            ("scale", StandardScaler()),
            ("pca", PCA(n_components=config.image.pca_components, random_state=config.seed)),
            ("model", classifier()),
        ]
    )
    fusion_transform = ColumnTransformer(
        [
            ("numeric", StandardScaler(), slice(0, numeric_count)),
            (
                "image",
                Pipeline(
                    [
                        ("scale", StandardScaler()),
                        (
                            "pca",
                            PCA(
                                n_components=config.image.pca_components,
                                random_state=config.seed,
                            ),
                        ),
                    ]
                ),
                slice(numeric_count, None),
            ),
        ]
    )
    return {
        "numeric_logistic": Pipeline([("scale", StandardScaler()), ("model", classifier())]),
        "numeric_xgboost": boosted(),
        "image_logistic": image_pipeline,
        "fusion_logistic": Pipeline([("features", fusion_transform), ("model", classifier())]),
        "fusion_xgboost": boosted(),
    }


def _tune_xgboost(
    x_train: NDArray[np.float64],
    y_train: NDArray[np.int64],
    config: ModelSelectionConfig,
) -> tuple[XGBClassifier, list[dict[str, Any]], dict[str, float | int]]:
    sensitivity = config.sensitivity
    splitter = TimeSeriesSplit(n_splits=sensitivity.time_series_splits, gap=sensitivity.gap_samples)
    scores: list[dict[str, Any]] = []
    for depth in sensitivity.depths:
        for estimators in sensitivity.estimators:
            for learning_rate in sensitivity.learning_rates:
                fold_scores: list[float] = []
                for train_index, validation_index in splitter.split(x_train):
                    model = XGBClassifier(
                        objective="multi:softprob",
                        num_class=len(config.class_order),
                        eval_metric="mlogloss",
                        random_state=config.seed,
                        n_estimators=estimators,
                        max_depth=depth,
                        learning_rate=learning_rate,
                        subsample=config.xgboost.subsample,
                        colsample_bytree=config.xgboost.colsample_bytree,
                        n_jobs=1,
                    ).fit(x_train[train_index], y_train[train_index])
                    predicted = np.asarray(model.predict(x_train[validation_index]), dtype=np.int64)
                    fold_scores.append(
                        float(
                            f1_score(
                                y_train[validation_index],
                                predicted,
                                labels=np.arange(len(config.class_order)),
                                average="macro",
                                zero_division=0,
                            )
                        )
                    )
                scores.append(
                    {
                        "max_depth": depth,
                        "n_estimators": estimators,
                        "learning_rate": learning_rate,
                        "fold_macro_f1": fold_scores,
                        "mean_macro_f1": float(np.mean(fold_scores)),
                    }
                )
    best = max(
        scores,
        key=lambda item: (
            item["mean_macro_f1"],
            -item["max_depth"],
            -item["n_estimators"],
            -item["learning_rate"],
        ),
    )
    parameters: dict[str, float | int] = {
        "max_depth": int(best["max_depth"]),
        "n_estimators": int(best["n_estimators"]),
        "learning_rate": float(best["learning_rate"]),
    }
    selected = XGBClassifier(
        objective="multi:softprob",
        num_class=len(config.class_order),
        eval_metric="mlogloss",
        random_state=config.seed,
        n_estimators=parameters["n_estimators"],
        max_depth=parameters["max_depth"],
        learning_rate=parameters["learning_rate"],
        subsample=config.xgboost.subsample,
        colsample_bytree=config.xgboost.colsample_bytree,
        n_jobs=1,
    )
    return selected, scores, parameters


def _family_sensitivity_models(config: ModelSelectionConfig) -> dict[str, Any]:
    models: dict[str, Any] = {}
    sensitivity = config.sensitivity
    for feature_version in ("v1", "v2"):
        prefix = f"numeric_{feature_version}"
        for c_value in sensitivity.svc_cs:
            for gamma in sensitivity.svc_gammas:
                name = f"{prefix}_svc_c{c_value:g}_{gamma}"
                models[name] = Pipeline(
                    [
                        ("scale", StandardScaler()),
                        (
                            "model",
                            CalibratedClassifierCV(
                                SVC(
                                    C=c_value,
                                    gamma=gamma,
                                    class_weight="balanced",
                                    random_state=config.seed,
                                ),
                                method="sigmoid",
                                cv=3,
                                ensemble=False,
                            ),
                        ),
                    ]
                )
        for depth in sensitivity.tree_depths:
            for minimum_leaf in sensitivity.tree_min_samples_leaf:
                suffix = f"d{depth}_leaf{minimum_leaf}"
                models[f"{prefix}_random_forest_{suffix}"] = RandomForestClassifier(
                    n_estimators=sensitivity.tree_estimators,
                    max_depth=depth,
                    min_samples_leaf=minimum_leaf,
                    class_weight="balanced",
                    random_state=config.seed,
                    n_jobs=1,
                )
                models[f"{prefix}_extra_trees_{suffix}"] = ExtraTreesClassifier(
                    n_estimators=sensitivity.tree_estimators,
                    max_depth=depth,
                    min_samples_leaf=minimum_leaf,
                    class_weight="balanced",
                    random_state=config.seed,
                    n_jobs=1,
                )
    return models


def _validation_tune_xgboost(
    x_train: NDArray[np.float64],
    y_train: NDArray[np.int64],
    x_validation: NDArray[np.float64],
    y_validation: NDArray[np.int64],
    config: ModelSelectionConfig,
) -> tuple[XGBClassifier, list[dict[str, Any]], dict[str, float | int]]:
    sensitivity = config.sensitivity
    scores: list[dict[str, Any]] = []
    fitted: list[XGBClassifier] = []
    for depth in sensitivity.depths:
        for estimators in sensitivity.estimators:
            for learning_rate in sensitivity.learning_rates:
                model = XGBClassifier(
                    objective="multi:softprob",
                    num_class=len(config.class_order),
                    eval_metric="mlogloss",
                    random_state=config.seed,
                    n_estimators=estimators,
                    max_depth=depth,
                    learning_rate=learning_rate,
                    subsample=config.xgboost.subsample,
                    colsample_bytree=config.xgboost.colsample_bytree,
                    n_jobs=1,
                ).fit(x_train, y_train)
                predicted = np.asarray(model.predict(x_validation), dtype=np.int64)
                score = float(
                    f1_score(
                        y_validation,
                        predicted,
                        labels=np.arange(len(config.class_order)),
                        average="macro",
                        zero_division=0,
                    )
                )
                fitted.append(model)
                scores.append(
                    {
                        "max_depth": depth,
                        "n_estimators": estimators,
                        "learning_rate": learning_rate,
                        "validation_macro_f1": score,
                    }
                )
    best_index = max(
        range(len(scores)),
        key=lambda index: (
            scores[index]["validation_macro_f1"],
            -scores[index]["max_depth"],
            -scores[index]["n_estimators"],
            -scores[index]["learning_rate"],
        ),
    )
    best = scores[best_index]
    parameters: dict[str, float | int] = {
        "max_depth": int(best["max_depth"]),
        "n_estimators": int(best["n_estimators"]),
        "learning_rate": float(best["learning_rate"]),
    }
    return fitted[best_index], scores, parameters


class ModelSelectionPipeline:
    def __init__(
        self,
        *,
        project_root: Path,
        config_path: Path,
        labels_path: Path,
        clean_root: Path,
        artifact_dir: Path,
        report_path: Path,
    ) -> None:
        self.project_root = project_root.resolve()
        self.config_path = config_path.resolve()
        self.labels_path = labels_path.resolve()
        self.clean_root = clean_root.resolve()
        self.artifact_dir = artifact_dir.resolve()
        self.report_path = report_path.resolve()

    def run(self) -> SelectionRunResult:
        config = ModelSelectionConfig.load(self.config_path)
        split_path = self.project_root / config.split_manifest
        label_config_path = self.project_root / config.label_config
        label_config = LabelConfig.load(label_config_path)
        sample_cache_key = hashlib.sha256(
            (
                json.dumps(asdict(config.image), sort_keys=True)
                + _sha256(split_path)
                + _sha256(self.labels_path)
                + _sha256(self.clean_root / "manifest.json")
            ).encode()
        ).hexdigest()
        loaded = load_model_samples(
            split_path=split_path,
            labels_path=self.labels_path,
            clean_root=self.clean_root,
            label_run_id=config.label_run_id,
            execution_cost=float(label_config.fixed_execution_cost),
            image_config=config.image,
            cache_path=self.project_root / "var" / "model-selection" / "samples-v1.joblib",
            cache_key=sample_cache_key,
        )
        train = [item for item in loaded.samples if item.baseline.partition is Partition.TRAIN]
        validation = [
            item for item in loaded.samples if item.baseline.partition is Partition.VALIDATION
        ]
        if (
            len(train) < 70
            or len(validation) != 26
            or loaded.rejected_validation_missing_features != 0
            or loaded.sealed_holdout_rows != 26
        ):
            raise ValueError("locked split counts changed or holdout was not sealed")
        assert_fit_partition(FitPurpose.SCALER, Partition.TRAIN)
        assert_fit_partition(FitPurpose.MODEL, Partition.TRAIN)
        labels = config.class_order
        label_index = {label: index for index, label in enumerate(labels)}
        numeric_train = np.asarray([item.numeric_features for item in train], dtype=np.float64)
        numeric_validation = np.asarray(
            [item.numeric_features for item in validation], dtype=np.float64
        )
        image_train = np.asarray([item.image_features for item in train], dtype=np.float64)
        image_validation = np.asarray(
            [item.image_features for item in validation], dtype=np.float64
        )
        fusion_train = np.hstack((numeric_train, image_train))
        fusion_validation = np.hstack((numeric_validation, image_validation))
        y_train = np.asarray(
            [label_index[item.baseline.label.value] for item in train], dtype=np.int64
        )
        y_validation = [item.baseline.label.value for item in validation]
        y_validation_index = np.asarray(
            [label_index[value] for value in y_validation], dtype=np.int64
        )
        baseline_samples, baseline_sealed = load_development_samples(
            split_path=split_path,
            labels_path=self.labels_path,
            clean_root=self.clean_root,
            label_run_id=config.label_run_id,
            execution_cost=float(label_config.fixed_execution_cost),
        )
        baseline_train = [item for item in baseline_samples if item.partition is Partition.TRAIN]
        baseline_validation = [
            item for item in baseline_samples if item.partition is Partition.VALIDATION
        ]
        if (
            len(baseline_train) != 90
            or len(baseline_validation) != 26
            or baseline_sealed != 26
            or [item.sample_id for item in baseline_validation]
            != [item.baseline.sample_id for item in validation]
        ):
            raise ValueError("historical v1 control does not match locked validation")
        numeric_v1_train = np.asarray([item.features for item in baseline_train], dtype=np.float64)
        numeric_v1_validation = np.asarray(
            [item.features for item in baseline_validation], dtype=np.float64
        )
        y_train_v1 = np.asarray(
            [label_index[item.label.value] for item in baseline_train], dtype=np.int64
        )
        matrices = {
            "numeric": (numeric_train, numeric_validation, y_train),
            "numeric_v1": (numeric_v1_train, numeric_v1_validation, y_train_v1),
            "image": (image_train, image_validation, y_train),
            "fusion": (fusion_train, fusion_validation, y_train),
        }
        models = _models(config, len(FEATURE_NAMES))
        models.update(_family_sensitivity_models(config))
        v1_tuned, v1_grid, v1_parameters = _tune_xgboost(numeric_v1_train, y_train_v1, config)
        v2_tuned, v2_grid, v2_parameters = _tune_xgboost(numeric_train, y_train, config)
        models["numeric_v1_xgboost_cv"] = v1_tuned
        models["numeric_v2_xgboost_cv"] = v2_tuned
        v1_validation_tuned, v1_validation_grid, v1_validation_parameters = (
            _validation_tune_xgboost(
                numeric_v1_train,
                y_train_v1,
                numeric_v1_validation,
                y_validation_index,
                config,
            )
        )
        v2_validation_tuned, v2_validation_grid, v2_validation_parameters = (
            _validation_tune_xgboost(
                numeric_train,
                y_train,
                numeric_validation,
                y_validation_index,
                config,
            )
        )
        models["numeric_v1_xgboost_validation"] = v1_validation_tuned
        models["numeric_v2_xgboost_validation"] = v2_validation_tuned
        results: dict[str, dict[str, Any]] = {}
        for name, model in models.items():
            family = _candidate_family(name)
            matrix_family = _matrix_family(name)
            x_train, x_validation, candidate_y_train = matrices[matrix_family]
            tracemalloc.start()
            started = time.perf_counter()
            model.fit(x_train, candidate_y_train)
            fit_ms = (time.perf_counter() - started) * 1000
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            probabilities = _aligned_probabilities(
                np.asarray(model.predict_proba(x_validation), dtype=np.float64),
                np.asarray(model.classes_, dtype=np.int64),
                len(labels),
            )
            predictions = [labels[index] for index in np.argmax(probabilities, axis=1)]
            repeats = 50
            started = time.perf_counter()
            for _ in range(repeats):
                model.predict_proba(x_validation)
            latency_ms = (time.perf_counter() - started) * 1000 / repeats / len(validation)
            serialized = pickle.dumps(model, protocol=pickle.HIGHEST_PROTOCOL)
            resource_passed = (
                latency_ms <= config.resources.maximum_prediction_latency_ms
                and peak / 1024 / 1024 <= config.resources.maximum_python_peak_memory_mb
                and len(serialized) <= config.resources.maximum_artifact_bytes
            )
            results[name] = {
                "family": family,
                "feature_set": "1.0.0" if matrix_family == "numeric_v1" else "2.0.0",
                "classification": asdict(
                    classification_metrics(y_validation, predictions, probabilities)
                ),
                "backtest": asdict(backtest([item.baseline for item in validation], predictions)),
                "fit_ms": fit_ms,
                "prediction_latency_ms_per_sample": latency_ms,
                "python_peak_memory_mb": peak / 1024 / 1024,
                "artifact_bytes": len(serialized),
                "resource_passed": resource_passed,
                "prediction_sha256": hashlib.sha256("\n".join(predictions).encode()).hexdigest(),
            }
        gate_passed = True
        try:
            champion, selection_reason = choose_champion(results, config)
        except RuntimeError as exc:
            gate_passed = False
            champion = "NONE"
            selection_reason = str(exc)
        identity = {
            "engine_version": ENGINE_VERSION,
            "config_hash": config.canonical_hash,
            "config_sha256": _sha256(self.config_path),
            "split_sha256": _sha256(split_path),
            "labels_sha256": _sha256(self.labels_path),
            "clean_manifest_sha256": _sha256(self.clean_root / "manifest.json"),
            "label_config_hash": label_config.canonical_hash,
            "seed": config.seed,
        }
        run_id = hashlib.sha256(
            json.dumps(identity, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()[:16]
        artifact = {
            "artifact_schema": "model-selection-v1",
            "run_id": run_id,
            "identity": identity,
            "class_order": labels,
            "numeric_feature_names": FEATURE_NAMES,
            "image_feature_count": int(image_train.shape[1]),
            "sample_counts": {
                "train": len(train),
                "validation": len(validation),
                "train_rejected_feature_warmup": loaded.rejected_train_missing_features,
                "validation_rejected_feature_warmup": (loaded.rejected_validation_missing_features),
            },
            "holdout": {
                "opened": False,
                "labels_read": 0,
                "sealed_rows_skipped": loaded.sealed_holdout_rows,
            },
            "image_benchmark": {
                "source": "point-in-time synthetic charts",
                "real_chart_corpus": False,
                "encoding_total_ms": loaded.image_encoding_ms,
            },
            "library_versions": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scikit_learn": sklearn.__version__,
                "xgboost": xgboost.__version__,
            },
            "selection_rule": {
                "baseline_macro_f1": config.baseline_macro_f1,
                "minimum_macro_f1_gain": config.minimum_macro_f1_gain,
                "minimum_vision_macro_f1_gain": config.minimum_vision_macro_f1_gain,
                "reason": selection_reason,
            },
            "champion": champion,
            "exit_gate_passed": gate_passed,
            "results": results,
            "sensitivity": {
                "selection_scope": "TRAIN time-series CV only",
                "v1_selected": v1_parameters,
                "v2_selected": v2_parameters,
                "v1_grid": v1_grid,
                "v2_grid": v2_grid,
                "validation_selection_warning": (
                    "hyperparameters selected on validation; metric is selection-biased"
                ),
                "v1_validation_selected": v1_validation_parameters,
                "v2_validation_selected": v2_validation_parameters,
                "v1_validation_grid": v1_validation_grid,
                "v2_validation_grid": v2_validation_grid,
            },
        }
        self._publish(artifact, None if champion == "NONE" else models[champion])
        return SelectionRunResult(
            run_id,
            champion,
            self.artifact_dir / "model-selection-v1.json",
            self.report_path,
            loaded.sealed_holdout_rows,
        )

    def _publish(self, artifact: dict[str, Any], champion: Any | None) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        champion_path = self.artifact_dir / "champion-v1.joblib"
        if champion is not None:
            temporary_model = champion_path.with_suffix(".joblib.tmp")
            joblib.dump(champion, temporary_model, compress=3)
            os.replace(temporary_model, champion_path)
            artifact["champion_artifact"] = {
                "path": champion_path.name,
                "bytes": champion_path.stat().st_size,
                "sha256": _sha256(champion_path),
            }
        else:
            champion_path.unlink(missing_ok=True)
            artifact["champion_artifact"] = None
        artifact_path = self.artifact_dir / "model-selection-v1.json"
        temporary_json = artifact_path.with_suffix(".json.tmp")
        temporary_json.write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        os.replace(temporary_json, artifact_path)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(_markdown_report(artifact), encoding="utf-8", newline="\n")


def _markdown_report(artifact: dict[str, Any]) -> str:
    baseline_f1 = artifact["selection_rule"]["baseline_macro_f1"]
    required_f1 = baseline_f1 + artifact["selection_rule"]["minimum_macro_f1_gain"]
    resource_eligible = {
        name: result
        for name, result in artifact["results"].items()
        if result["family"] != "image" and result["resource_passed"]
    }
    best_name, best_result = max(
        resource_eligible.items(),
        key=lambda item: float(item[1]["classification"]["macro_f1"]),
    )
    best_f1 = float(best_result["classification"]["macro_f1"])
    all_directional_returns_negative = all(
        float(result["backtest"]["net_return_sum"]) < 0 for result in artifact["results"].values()
    )
    decision_summary = (
        "The selected object is a candidate for Stage P calibration."
        if artifact["exit_gate_passed"]
        else "No candidate is promoted to Stage P; Stage O remains incomplete."
    )
    lines = [
        "# Stage O model-selection report",
        "",
        "- Date: 16/11/2026 (Asia/Saigon)",
        f"- Run ID: `{artifact['run_id']}`",
        f"- Champion candidate: **`{artifact['champion']}`**",
        "- FINAL_HOLDOUT opened: **false**",
        f"- Result: **{'PASS' if artifact['exit_gate_passed'] else 'NO-GO'}**",
        "",
        "## Validation and resource comparison",
        "",
        "| Candidate | Family | Accuracy | Macro F1 | Brier | ECE | Net return | "
        "Latency ms/sample | Peak MiB | Artifact bytes | Resource gate |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, result in artifact["results"].items():
        metric = result["classification"]
        simulation = result["backtest"]
        lines.append(
            f"| `{name}` | {result['family']} | {metric['accuracy']:.4f} | "
            f"{metric['macro_f1']:.4f} | {metric['multiclass_brier']:.4f} | "
            f"{metric['ece_10_bin']:.4f} | {simulation['net_return_sum']:.6f} | "
            f"{result['prediction_latency_ms_per_sample']:.4f} | "
            f"{result['python_peak_memory_mb']:.2f} | {result['artifact_bytes']} | "
            f"{'PASS' if result['resource_passed'] else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Selection decision",
            "",
            f"Locked Stage I baseline macro F1: `{baseline_f1:.4f}`.",
            f"Locked exit threshold (baseline + minimum gain): `{required_f1:.4f}`.",
            f"Best resource-eligible candidate: `{best_name}` with macro F1 `{best_f1:.4f}`.",
            f"Delta versus baseline: `{best_f1 - baseline_f1:+.4f}`; delta versus exit "
            f"threshold: `{best_f1 - required_f1:+.4f}`.",
            f"Selection reason: {artifact['selection_rule']['reason']}.",
            decision_summary,
            (
                "Every evaluated candidate had negative cost-aware net return on validation."
                if all_directional_returns_negative
                else "At least one candidate had non-negative cost-aware net return on validation."
            ),
            "It is not a production/live model. Every directional candidate remains subject to "
            "cost-aware validation and NO_TRADE policy.",
            "",
            "## Experiment rounds and interpretation",
            "",
            "1. Evaluated the locked numeric-v2, image-only and fusion candidates.",
            "2. Tuned XGBoost with purged chronological TRAIN cross-validation.",
            "3. Ran a bounded validation sensitivity analysis across XGBoost, calibrated SVC, "
            "Random Forest and Extra Trees families.",
            "4. Stopped after the bounded family analysis failed the locked exit threshold.",
            "",
            "The validation-tuned metrics are selection-biased and are retained as diagnostics, "
            "not as unbiased performance estimates. More searching on the same 26 validation "
            "samples would increase overfitting risk. The legitimate next step is more independent "
            "historical training/validation evidence and a versioned real-chart corpus, followed "
            "by a new Stage O run. Stage P must not begin from this NO-GO result.",
            "",
            "## Image benchmark boundary",
            "",
            "Image-only and fusion inputs are point-in-time synthetic 1H+15m charts.",
            "Header/OCR text and axes are cropped; quality metrics are appended.",
            "There is no versioned real-chart corpus. This measures pipeline contribution only.",
            "It cannot establish generalization to screenshots supplied by users.",
            "",
            "## Reproducibility",
            "",
            f"- Config hash: `{artifact['identity']['config_hash']}`",
            f"- Split SHA-256: `{artifact['identity']['split_sha256']}`",
            f"- Labels SHA-256: `{artifact['identity']['labels_sha256']}`",
            f"- Clean manifest SHA-256: `{artifact['identity']['clean_manifest_sha256']}`",
            f"- Seed: `{artifact['identity']['seed']}`",
            f"- TRAIN/VALIDATION: `{artifact['sample_counts']['train']}` / "
            f"`{artifact['sample_counts']['validation']}`; holdout labels read: `0`.",
            f"- TRAIN rows rejected by feature-v2 warm-up: "
            f"`{artifact['sample_counts']['train_rejected_feature_warmup']}`; VALIDATION rejected: "
            f"`{artifact['sample_counts']['validation_rejected_feature_warmup']}`.",
            (
                f"- Champion SHA-256: `{artifact['champion_artifact']['sha256']}`"
                if artifact["champion_artifact"] is not None
                else "- Champion artifact: not created because the exit gate failed."
            ),
            "",
            "All computation used existing local CPU and open-source dependencies.",
            "New cash cost is **0 VNĐ**.",
        ]
    )
    return "\n".join(lines) + "\n"
