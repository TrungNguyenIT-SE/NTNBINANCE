"""Command-line entry point for Stage I baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ntnbinance.baselines.pipeline import BaselinePipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run locked leakage-safe Stage I baselines")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path("configs/baselines/baseline-v1.toml"))
    parser.add_argument("--labels", type=Path, required=True)
    parser.add_argument("--clean-root", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, default=Path("models/baselines"))
    parser.add_argument("--report", type=Path, default=Path("reports/baseline-v1.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.project_root.resolve()
    result = BaselinePipeline(
        project_root=root,
        config_path=root / args.config,
        labels_path=root / args.labels,
        clean_root=root / args.clean_root,
        artifact_dir=root / args.artifacts,
        report_path=root / args.report,
    ).run()
    print(
        json.dumps(
            {
                "artifact": str(result.artifact_path),
                "holdout": "SEALED",
                "run_id": result.run_id,
                "selected_baseline": result.selected_baseline,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
