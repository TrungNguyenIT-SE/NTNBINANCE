"""CLI for deterministic Stage G label generation."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from ntnbinance.labels.pipeline import LabelPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate versioned triple-barrier labels")
    parser.add_argument("--clean-root", type=Path, required=True)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument("--output-root", type=Path, default=Path("data/labels"))
    parser.add_argument(
        "--config", type=Path, default=Path("configs/labels/triple-barrier-v1.toml")
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = LabelPipeline(
        clean_root=args.clean_root,
        raw_root=args.raw_root,
        output_root=args.output_root,
        config_path=args.config,
    ).run()
    print(json.dumps(asdict(result), indent=2, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
