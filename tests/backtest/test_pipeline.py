from __future__ import annotations

import json
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from ntnbinance.backtest import pipeline
from ntnbinance.backtest.models import BacktestInput, Side
from ntnbinance.baselines.models import FEATURE_NAMES
from ntnbinance.labels.models import VolatilityRegime

from .helpers import candle


def _inputs() -> list[BacktestInput]:
    values: list[BacktestInput] = []
    for index in range(26):
        start = index * 3_600_000
        candles = tuple(
            replace(
                candle(minute, high="103", low="99", close="101", volume="100000"),
                open_time_ms=start + minute * 60_000,
                close_time_ms=start + minute * 60_000 + 59_999,
            )
            for minute in range(60)
        )
        values.append(
            BacktestInput(
                sample_id=f"sample-{index}",
                symbol="BTCUSDT" if index % 2 == 0 else "ETHUSDT",
                decision_time_ms=start,
                vertical_barrier_time_ms=start + 3_600_000,
                reference_price=Decimal(100),
                atr=Decimal(2),
                regime=VolatilityRegime.LOW if index % 2 == 0 else VolatilityRegime.NORMAL,
                features=tuple(float(index + feature) for feature in range(len(FEATURE_NAMES))),
                candles=candles,
                funding_events=(),
            )
        )
    return values


def _project(tmp_path: Path) -> tuple[Path, Path, Path]:
    project = tmp_path / "project"
    for folder in (
        project / "models" / "baselines",
        project / "data" / "manifests",
        project / "configs" / "labels",
    ):
        folder.mkdir(parents=True)
    (project / "models" / "baselines" / "baseline-v1.json").write_text(
        json.dumps(
            {
                "selected_baseline": "xgboost_cpu",
                "holdout": {"opened": False},
            }
        ),
        encoding="utf-8",
    )
    (project / "data" / "manifests" / "split-v1.json").write_text("{}", encoding="utf-8")
    (project / "data" / "manifests" / "exchange-info-stage-j.json").write_text(
        "{}", encoding="utf-8"
    )
    (project / "configs" / "labels" / "triple-barrier-v1.toml").write_text(
        Path("configs/labels/triple-barrier-v1.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    clean = project / "clean"
    raw = project / "raw"
    clean.mkdir()
    raw.mkdir()
    (clean / "manifest.json").write_text("{}", encoding="utf-8")
    (raw / "manifest.jsonl").write_text("{}\n", encoding="utf-8")
    config = project / "backtest.toml"
    config.write_text(
        Path("configs/backtest/backtest-v1.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return project, clean, raw


def test_pipeline_publishes_reproducible_stress_and_groups(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    project, clean, raw = _project(tmp_path)
    inputs = _inputs()
    predictions = [Side.NO_TRADE if index % 5 == 0 else Side.LONG for index in range(26)]
    confidences = [Decimal("0.55") for _ in inputs]
    monkeypatch.setattr(pipeline, "load_validation_inputs", lambda **_: inputs)
    monkeypatch.setattr(pipeline, "_predict", lambda *_: (predictions, confidences))
    runner = pipeline.BacktestPipeline(
        project_root=project,
        config_path=project / "backtest.toml",
        clean_root=clean,
        raw_root=raw,
        artifact_dir=project / "models" / "backtests",
        report_path=project / "report.md",
    )

    first = runner.run()
    first_bytes = first.artifact_path.read_bytes()
    second = runner.run()
    artifact = json.loads(first_bytes)

    assert first.run_id == second.run_id
    assert first_bytes == second.artifact_path.read_bytes()
    assert artifact["holdout"] == {"labels_read": 0, "opened": False}
    assert set(artifact["cost_stress"]) == {"1.0", "1.5", "2.0"}
    assert set(artifact["groups"]) == {"confidence", "month", "regime", "side", "symbol"}
    assert "NO-GO on trading edge" in first.report_path.read_text(encoding="utf-8")


def test_predict_and_pipeline_guards_reject_invalid_artifact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    with pytest.raises(ValueError, match="model or class order"):
        pipeline._predict({}, [(0.0,) * len(FEATURE_NAMES)])

    project, clean, raw = _project(tmp_path)
    baseline = project / "models" / "baselines" / "baseline-v1.json"
    baseline.write_text(
        json.dumps({"selected_baseline": "logistic_regression", "holdout": {"opened": False}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "load_validation_inputs", lambda **_: [])
    with pytest.raises(ValueError, match="XGBoost baseline"):
        pipeline.BacktestPipeline(
            project_root=project,
            config_path=project / "backtest.toml",
            clean_root=clean,
            raw_root=raw,
            artifact_dir=project / "artifacts",
            report_path=project / "report.md",
        ).run()
