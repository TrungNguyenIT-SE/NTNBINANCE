from pathlib import Path

import pytest

from ntnbinance.baselines import cli
from ntnbinance.baselines.pipeline import BaselineRunResult


def test_cli_runs_pipeline_and_reports_sealed_holdout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    class FakePipeline:
        def __init__(self, **_: object) -> None:
            pass

        def run(self) -> BaselineRunResult:
            return BaselineRunResult(
                "run-id",
                tmp_path / "artifact.json",
                tmp_path / "report.md",
                "xgboost_cpu",
                26,
            )

    monkeypatch.setattr(cli, "BaselinePipeline", FakePipeline)

    result = cli.main(
        [
            "--project-root",
            str(tmp_path),
            "--labels",
            "labels.jsonl",
            "--clean-root",
            "clean",
        ]
    )

    assert result == 0
    output = capsys.readouterr().out
    assert '"holdout": "SEALED"' in output
    assert '"selected_baseline": "xgboost_cpu"' in output
