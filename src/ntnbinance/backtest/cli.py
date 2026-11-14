"""CLI for the locked Stage J execution-aware backtest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ntnbinance.backtest.pipeline import BacktestPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Stage J execution-aware backtest")
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=Path("configs/backtest/backtest-v1.toml"))
    parser.add_argument("--clean-root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--artifacts", type=Path, default=Path("models/backtests"))
    parser.add_argument("--report", type=Path, default=Path("reports/backtest-validation.md"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.project_root.resolve()
    result = BacktestPipeline(
        project_root=root,
        config_path=root / args.config,
        clean_root=root / args.clean_root,
        raw_root=root / args.raw_root,
        artifact_dir=root / args.artifacts,
        report_path=root / args.report,
    ).run()
    print(
        json.dumps(
            {
                "artifact": str(result.artifact_path),
                "holdout": "SEALED",
                "net_pnl_usdt": result.base_metrics.net_pnl_usdt,
                "run_id": result.run_id,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
