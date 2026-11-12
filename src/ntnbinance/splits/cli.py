"""CLI for locking the Stage H split manifest."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from ntnbinance.splits.pipeline import SplitPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lock purged time splits and final holdout")
    parser.add_argument("--labels-root", type=Path, required=True)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/splits/purged-walk-forward-v1.toml")
    )
    parser.add_argument("--manifest", type=Path, default=Path("data/manifests/split-v1.json"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = SplitPipeline(
        labels_root=args.labels_root,
        config_path=args.config,
        manifest_path=args.manifest,
    ).run()
    print(json.dumps(asdict(result), indent=2, default=str, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
