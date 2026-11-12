"""Command line entry point for Stage F data-quality processing."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from ntnbinance.data_quality.comparison import compare_with_binance
from ntnbinance.data_quality.pipeline import DataQualityPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate raw data and publish clean Parquet")
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--clean-root", type=Path, default=Path("data/clean"))
    parser.add_argument("--quarantine-root", type=Path, default=Path("data/quarantine"))
    parser.add_argument("--compare-binance", action="store_true")
    parser.add_argument("--comparison-samples", type=int, default=1)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = DataQualityPipeline(
        raw_root=args.raw_root,
        clean_root=args.clean_root,
        quarantine_root=args.quarantine_root,
    ).run()
    output: dict[str, object] = {
        "clean_root": str(result.clean_root),
        "coverage": [asdict(item) for item in result.coverage],
        "excluded_resample_buckets": result.excluded_resample_buckets,
        "feature_coverage": [asdict(item) for item in result.feature_coverage],
        "quarantine_root": str(result.quarantine_root),
        "raw_dataset_counts": result.raw_dataset_counts,
        "reused": result.reused,
        "run_id": result.run_id,
        "stats": asdict(result.stats),
    }
    exit_code = 0
    if args.compare_binance:
        comparison = compare_with_binance(result.clean_root, per_group=args.comparison_samples)
        output["binance_comparison"] = comparison.to_dict()
        if comparison.mismatched:
            exit_code = 2
    print(json.dumps(output, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
