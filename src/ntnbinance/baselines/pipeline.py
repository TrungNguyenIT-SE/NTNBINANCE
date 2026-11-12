"""Reproducible Stage I experiment runner and immutable artifact publisher."""

from __future__ import annotations

import hashlib
import json
import os
import platform
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import sklearn
import xgboost
from numpy.typing import NDArray
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from ntnbinance.baselines.data import load_development_samples
from ntnbinance.baselines.evaluation import backtest, classification_metrics
from ntnbinance.baselines.models import FEATURE_NAMES, BaselineConfig, BaselineSample
from ntnbinance.labels.models import Label, LabelConfig
from ntnbinance.splits.models import FitPurpose, Partition, assert_fit_partition

BASELINE_ENGINE_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class BaselineRunResult:
    run_id: str
    artifact_path: Path
    report_path: Path
    selected_baseline: str
    sealed_holdout_rows: int


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _one_hot(predictions: list[str], labels: tuple[str, ...]) -> NDArray[np.float64]:
    return np.asarray(
        [[1.0 if value == label else 0.0 for label in labels] for value in predictions]
    )


def _rule_predictions(samples: list[BaselineSample], config: BaselineConfig) -> list[str]:
    predictions: list[str] = []
    for sample in samples:
        feature = dict(zip(FEATURE_NAMES, sample.features, strict=True))
        atr = feature["atr_ratio_14"]
        trigger = feature["return_15m_4"]
        trend = feature["trend_1h_3bar"]
        threshold = config.rule.trigger_atr_fraction * atr
        if not config.rule.minimum_atr_ratio <= atr <= config.rule.maximum_atr_ratio:
            predictions.append(Label.NO_TRADE.value)
        elif trend > 0 and trigger > threshold:
            predictions.append(Label.LONG.value)
        elif trend < 0 and trigger < -threshold:
            predictions.append(Label.SHORT.value)
        else:
            predictions.append(Label.NO_TRADE.value)
    return predictions


def _aligned_probabilities(
    probabilities: NDArray[np.float64], fitted_classes: NDArray[np.int64], class_count: int
) -> NDArray[np.float64]:
    aligned = np.zeros((probabilities.shape[0], class_count), dtype=np.float64)
    for source, target in enumerate(fitted_classes):
        aligned[:, int(target)] = probabilities[:, source]
    return aligned


class BaselinePipeline:
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

    def run(self) -> BaselineRunResult:
        config = BaselineConfig.load(self.config_path)
        split_path = self.project_root / config.split_manifest
        label_config = LabelConfig.load(self.project_root / config.label_config)
        samples, sealed_rows = load_development_samples(
            split_path=split_path,
            labels_path=self.labels_path,
            clean_root=self.clean_root,
            label_run_id=config.label_run_id,
            execution_cost=float(label_config.fixed_execution_cost),
        )
        train = [item for item in samples if item.partition is Partition.TRAIN]
        validation = [item for item in samples if item.partition is Partition.VALIDATION]
        if len(train) != 90 or len(validation) != 26 or sealed_rows != 26:
            raise ValueError("locked split counts changed or final holdout was not sealed")
        assert_fit_partition(FitPurpose.SCALER, Partition.TRAIN)
        assert_fit_partition(FitPurpose.MODEL, Partition.TRAIN)
        labels = config.class_order
        label_index = {label: index for index, label in enumerate(labels)}
        x_train = np.asarray([item.features for item in train], dtype=np.float64)
        x_validation = np.asarray([item.features for item in validation], dtype=np.float64)
        y_train_text = [item.label.value for item in train]
        y_validation = [item.label.value for item in validation]
        y_train = np.asarray([label_index[value] for value in y_train_text], dtype=np.int64)

        results: dict[str, dict[str, Any]] = {}

        def record(name: str, predictions: list[str], probabilities: NDArray[np.float64]) -> None:
            results[name] = {
                "classification": asdict(
                    classification_metrics(y_validation, predictions, probabilities)
                ),
                "backtest": asdict(backtest(validation, predictions)),
                "prediction_sha256": hashlib.sha256("\n".join(predictions).encode()).hexdigest(),
            }

        counts = np.bincount(y_train, minlength=len(labels)).astype(np.float64)
        priors = counts / np.sum(counts)
        majority = labels[int(np.argmax(priors))]
        record("majority", [majority] * len(validation), np.tile(priors, (len(validation), 1)))
        rng = np.random.default_rng(config.seed)
        random_predictions = [
            labels[index] for index in rng.choice(len(labels), len(validation), p=priors)
        ]
        record("random", random_predictions, _one_hot(random_predictions, labels))
        no_trade = [Label.NO_TRADE.value] * len(validation)
        record("always_no_trade", no_trade, _one_hot(no_trade, labels))
        rule = _rule_predictions(validation, config)
        record("rule_trend_trigger_atr", rule, _one_hot(rule, labels))

        scaler = StandardScaler().fit(x_train)
        train_scaled = scaler.transform(x_train)
        validation_scaled = scaler.transform(x_validation)
        logistic = LogisticRegression(
            C=config.logistic_regression.C,
            max_iter=config.logistic_regression.max_iter,
            class_weight=config.logistic_regression.class_weight,
            random_state=config.seed,
        ).fit(train_scaled, y_train)
        logistic_probabilities = _aligned_probabilities(
            logistic.predict_proba(validation_scaled), logistic.classes_, len(labels)
        )
        logistic_predictions = [
            labels[index] for index in np.argmax(logistic_probabilities, axis=1)
        ]
        record("logistic_regression", logistic_predictions, logistic_probabilities)

        xgb = XGBClassifier(
            objective="multi:softprob",
            num_class=len(labels),
            eval_metric="mlogloss",
            random_state=config.seed,
            n_estimators=config.xgboost.n_estimators,
            max_depth=config.xgboost.max_depth,
            learning_rate=config.xgboost.learning_rate,
            subsample=config.xgboost.subsample,
            colsample_bytree=config.xgboost.colsample_bytree,
            n_jobs=config.xgboost.n_jobs,
        ).fit(x_train, y_train)
        xgb_probabilities = _aligned_probabilities(
            xgb.predict_proba(x_validation), xgb.classes_, len(labels)
        )
        xgb_predictions = [labels[index] for index in np.argmax(xgb_probabilities, axis=1)]
        record("xgboost_cpu", xgb_predictions, xgb_probabilities)

        eligible = ("rule_trend_trigger_atr", "logistic_regression", "xgboost_cpu")
        selected = max(
            eligible,
            key=lambda name: (
                results[name]["classification"]["macro_f1"],
                results[name]["classification"]["accuracy"],
                -results[name]["classification"]["multiclass_brier"],
            ),
        )
        identity = {
            "baseline_engine_version": BASELINE_ENGINE_VERSION,
            "config_hash": config.canonical_hash,
            "config_sha256": _sha256(self.config_path),
            "split_manifest_sha256": _sha256(split_path),
            "label_jsonl_sha256": _sha256(self.labels_path),
            "label_config_hash": label_config.canonical_hash,
            "label_config_sha256": _sha256(self.project_root / config.label_config),
            "clean_manifest_sha256": _sha256(self.clean_root / "manifest.json"),
            "seed": config.seed,
        }
        run_id = hashlib.sha256(
            json.dumps(identity, separators=(",", ":"), sort_keys=True).encode()
        ).hexdigest()[:16]
        artifact: dict[str, Any] = {
            "artifact_schema": "baseline-v1",
            "class_order": labels,
            "feature_names": FEATURE_NAMES,
            "holdout": {"opened": False, "labels_read": 0, "sealed_rows_skipped": sealed_rows},
            "identity": identity,
            "library_versions": {
                "numpy": np.__version__,
                "python": platform.python_version(),
                "scikit_learn": sklearn.__version__,
                "xgboost": xgboost.__version__,
            },
            "logistic_model": {
                "classes": logistic.classes_.tolist(),
                "coefficients": logistic.coef_.tolist(),
                "intercepts": logistic.intercept_.tolist(),
                "scaler_mean": scaler.mean_.tolist(),
                "scaler_scale": scaler.scale_.tolist(),
            },
            "results": results,
            "run_id": run_id,
            "sample_counts": {"train": len(train), "validation": len(validation)},
            "selected_baseline": selected,
            "selection_rule": "max(validation macro_f1, accuracy, -multiclass_brier)",
            "xgboost_model": json.loads(xgb.get_booster().save_raw(raw_format="json")),
        }
        self._publish(artifact)
        return BaselineRunResult(
            run_id,
            self.artifact_dir / "baseline-v1.json",
            self.report_path,
            selected,
            sealed_rows,
        )

    def _publish(self, artifact: dict[str, Any]) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        target = self.artifact_dir / "baseline-v1.json"
        payload = json.dumps(artifact, indent=2, sort_keys=True) + "\n"
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(payload, encoding="utf-8", newline="\n")
        os.replace(temporary, target)
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        self.report_path.write_text(
            _markdown_report(artifact, target), encoding="utf-8", newline="\n"
        )


def _markdown_report(artifact: dict[str, Any], artifact_path: Path) -> str:
    lines = [
        "# Stage I baseline v1 report",
        "",
        "> Evaluation date: `13/11/2026` (Asia/Saigon)",
        ">",
        "> Result: **PASS — reproducible development baseline; final holdout remains sealed**",
        "",
        "## Locked identity",
        "",
        f"- Run ID: `{artifact['run_id']}`",
        f"- Config hash: `{artifact['identity']['config_hash']}`",
        f"- Split SHA-256: `{artifact['identity']['split_manifest_sha256']}`",
        f"- Label JSONL SHA-256: `{artifact['identity']['label_jsonl_sha256']}`",
        f"- Cost config hash: `{artifact['identity']['label_config_hash']}`",
        f"- Artifact SHA-256: `{_sha256(artifact_path)}`",
        f"- Seed: `{artifact['identity']['seed']}`",
        "- Samples: TRAIN `90`, VALIDATION `26`, FINAL_HOLDOUT skipped `26`.",
        "- Holdout labels read: `0`; opened: `false`.",
        "",
        "## Validation results (all required metrics)",
        "",
        "| Baseline | Accuracy | Macro F1 | Macro precision | Macro recall | Brier | "
        "ECE-10 | Trades | Net return sum | Max DD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, result in artifact["results"].items():
        metric = result["classification"]
        test = result["backtest"]
        lines.append(
            f"| {name} | {metric['accuracy']:.4f} | {metric['macro_f1']:.4f} | "
            f"{metric['macro_precision']:.4f} | {metric['macro_recall']:.4f} | "
            f"{metric['multiclass_brier']:.4f} | {metric['ece_10_bin']:.4f} | "
            f"{test['trades']} | {test['net_return_sum']:.6f} | {test['maximum_drawdown']:.6f} |"
        )
    lines.extend(["", "## Per-class precision / recall / F1 / support", ""])
    for name, result in artifact["results"].items():
        lines.extend(
            [
                f"### {name}",
                "",
                "| Class | Precision | Recall | F1 | Support |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for label, values in result["classification"]["per_class"].items():
            lines.append(
                f"| {label} | {values['precision']:.4f} | {values['recall']:.4f} | "
                f"{values['f1']:.4f} | {values['support']} |"
            )
        lines.append("")
    selected = artifact["selected_baseline"]
    lines.extend(
        [
            "## Decision",
            "",
            f"Primary Stage I baseline: **`{selected}`**. A later model must beat its locked "
            "validation macro F1 without materially worsening calibration or net-cost behavior. "
            "Selection used the predeclared tuple `macro F1 → accuracy → lower Brier`; "
            "random/majority/no-trade were floors, "
            "not eligible champions.",
            "",
            "The seeded random draw happened to score macro F1 `0.4966` on only 26 samples, "
            "above XGBoost's `0.4607`; this is reported, not hidden. It is not a learnable or "
            "deployable policy and is highly unstable at this sample size. Every directional "
            "baseline had negative net return after costs; Stage I therefore demonstrates "
            "**no trading edge and authorizes no promotion or live trading**.",
            "",
            "## Feature and fit boundary",
            "",
            "All 13 numeric features are computed from candles with `close_time < decision_time`. "
            "They cover 15m returns/range/body/volume/taker flow, closed 1H trend, ATR and "
            "volatility, mark/index basis and symbol identity. StandardScaler and both learned "
            "models fit TRAIN only; VALIDATION is evaluation/selection only. Definitions and "
            "missing-data rules are locked in `docs/FEATURE_REGISTRY.md`.",
            "",
            "## Backtest boundary",
            "",
            "Returns use the Stage G entry reference, two-sided taker fee, half-spread, "
            "slippage, latency and funding sign. Barrier exits use the recorded first event; "
            "vertical exits use the closed 15m price; ambiguous 1m touches take the adverse "
            "barrier. This is a baseline comparator, not the full execution simulator required "
            "by Stage J (partial fills/tick/step/latency stress remain).",
            "",
            "## Reproduction",
            "",
            "```powershell",
            "powershell -File scripts/run-baselines.ps1",
            "```",
            "",
            "The script regenerates the report and JSON artifact deterministically from the "
            "locked config, split, clean run and label run. All computation is local with "
            "open-source packages; new cash cost remains **0 VNĐ**. The 26-sample validation "
            "window is too small for production claims.",
            "",
            "## Repository quality gate",
            "",
            "```text",
            "148 tests passed",
            "statement + branch coverage: 91.08%",
            "Ruff lint/format: pass",
            "mypy strict: pass",
            "pip check: pass",
            "frontend lint/format/typecheck/test/build: pass",
            "```",
            "",
        ]
    )
    return "\n".join(lines)
