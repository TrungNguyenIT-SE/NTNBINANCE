from __future__ import annotations

from pathlib import Path

from ntnbinance.data_quality.cli import build_parser


def test_cli_defaults_and_comparison_options() -> None:
    args = build_parser().parse_args(["--compare-binance", "--comparison-samples", "2"])
    assert args.raw_root == Path("data/raw")
    assert args.clean_root == Path("data/clean")
    assert args.quarantine_root == Path("data/quarantine")
    assert args.compare_binance
    assert args.comparison_samples == 2
