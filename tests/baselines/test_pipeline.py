from __future__ import annotations

import json
from pathlib import Path

import pytest

from ntnbinance.baselines import pipeline
from ntnbinance.baselines.models import BaselineSample
from ntnbinance.labels.models import Label, LabelReason
from ntnbinance.splits.models import Partition


def _samples() -> list[BaselineSample]:
    values: list[BaselineSample] = []
    labels = tuple(Label)
    for partition, count, offset in (
        (Partition.TRAIN, 90, 0),
        (Partition.VALIDATION, 26, 100),
    ):
        for index in range(count):
            label = labels[index % len(labels)]
            reason = {
                Label.LONG: LabelReason.UPPER_BARRIER_NET_POSITIVE,
                Label.SHORT: LabelReason.LOWER_BARRIER_NET_POSITIVE,
                Label.NO_TRADE: LabelReason.VERTICAL_BARRIER,
            }[label]
            values.append(
                BaselineSample(
                    sample_id=f"{partition.value}-{index}",
                    partition=partition,
                    symbol="ETHUSDT" if index % 2 else "BTCUSDT",
                    decision_time_ms=offset + index,
                    vertical_barrier_time_ms=offset + index + 60,
                    label=label,
                    reason=reason,
                    reference_price=100.0,
                    upper_barrier=101.0,
                    lower_barrier=99.0,
                    barrier_time_ms=offset + index + 30,
                    execution_cost=0.001,
                    funding_cost=0.0,
                    vertical_close=100.2,
                    features=tuple(((index + feature * 3) % 19) / 1000 for feature in range(13)),
                )
            )
    return values


def test_pipeline_is_deterministic_and_publishes_complete_artifact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project = tmp_path / "project"
    (project / "data" / "manifests").mkdir(parents=True)
    split = project / "data" / "manifests" / "split-v1.json"
    split.write_text("{}\n", encoding="utf-8")
    config = project / "baseline.toml"
    config.write_text(
        Path("configs/baselines/baseline-v1.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    labels = project / "labels.jsonl"
    labels.write_text("locked labels\n", encoding="utf-8")
    clean = project / "clean"
    clean.mkdir()
    (clean / "manifest.json").write_text("{}\n", encoding="utf-8")
    (project / "configs" / "labels").mkdir(parents=True)
    (project / "configs" / "labels" / "triple-barrier-v1.toml").write_text(
        Path("configs/labels/triple-barrier-v1.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "load_development_samples", lambda **_: (_samples(), 26))
    runner = pipeline.BaselinePipeline(
        project_root=project,
        config_path=config,
        labels_path=labels,
        clean_root=clean,
        artifact_dir=project / "models",
        report_path=project / "report.md",
    )

    first = runner.run()
    first_bytes = first.artifact_path.read_bytes()
    second = runner.run()

    assert first.run_id == second.run_id
    assert first_bytes == second.artifact_path.read_bytes()
    artifact = json.loads(first_bytes)
    assert set(artifact["results"]) == {
        "majority",
        "random",
        "always_no_trade",
        "rule_trend_trigger_atr",
        "logistic_regression",
        "xgboost_cpu",
    }
    assert artifact["holdout"] == {
        "labels_read": 0,
        "opened": False,
        "sealed_rows_skipped": 26,
    }
    assert "Primary Stage I baseline" in first.report_path.read_text(encoding="utf-8")


def test_pipeline_rejects_changed_split_counts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project = tmp_path
    (project / "data" / "manifests").mkdir(parents=True)
    (project / "data" / "manifests" / "split-v1.json").write_text("{}", encoding="utf-8")
    config = project / "baseline.toml"
    config.write_text(
        Path("configs/baselines/baseline-v1.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    labels = project / "labels"
    labels.write_text("x", encoding="utf-8")
    clean = project / "clean"
    clean.mkdir()
    (clean / "manifest.json").write_text("{}", encoding="utf-8")
    (project / "configs" / "labels").mkdir(parents=True)
    (project / "configs" / "labels" / "triple-barrier-v1.toml").write_text(
        Path("configs/labels/triple-barrier-v1.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "load_development_samples", lambda **_: ([], 0))

    with pytest.raises(ValueError, match="locked split counts"):
        pipeline.BaselinePipeline(
            project_root=project,
            config_path=config,
            labels_path=labels,
            clean_root=clean,
            artifact_dir=project / "models",
            report_path=project / "report.md",
        ).run()
