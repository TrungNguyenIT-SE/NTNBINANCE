from __future__ import annotations

import json
from pathlib import Path

import pytest

from ntnbinance.splits.cli import build_parser, main

from .helpers import CONFIG_PATH, label_artifact


def test_cli_defaults_and_real_manifest_generation(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    labels = label_artifact(tmp_path / "labels")
    manifest = tmp_path / "split.json"
    args = build_parser().parse_args(["--labels-root", str(labels)])
    assert args.config == CONFIG_PATH
    assert args.manifest == Path("data/manifests/split-v1.json")
    assert (
        main(
            [
                "--labels-root",
                str(labels),
                "--config",
                str(CONFIG_PATH),
                "--manifest",
                str(manifest),
            ]
        )
        == 0
    )
    output = capsys.readouterr()
    result = json.loads(output.out)
    assert result["counts"]["FINAL_HOLDOUT"] == 26
    assert manifest.is_file()
