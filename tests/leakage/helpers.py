from __future__ import annotations

import json
from pathlib import Path

from ntnbinance.splits.models import SampleWindow, SplitConfig

CONFIG_PATH = Path("configs/splits/purged-walk-forward-v1.toml")


def config() -> SplitConfig:
    return SplitConfig.load(CONFIG_PATH)


def sample_windows(count: int = 77) -> list[SampleWindow]:
    output: list[SampleWindow] = []
    for index in range(count):
        decision = index * 900_000
        for symbol in ("BTCUSDT", "ETHUSDT"):
            sample_id = f"{symbol}-{index:03d}"
            output.append(
                SampleWindow(
                    sample_id=sample_id,
                    origin_sample_id=sample_id,
                    symbol=symbol,
                    decision_time_ms=decision,
                    vertical_barrier_time_ms=decision + 3_600_000,
                )
            )
    return output


def label_artifact(root: Path) -> Path:
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "config_hash": "c" * 64,
                "config_version": "1.0.0",
                "run_id": "label-fixture",
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    labels = ("LONG", "SHORT", "NO_TRADE")
    with (root / "labels.jsonl").open("w", encoding="utf-8", newline="\n") as target:
        for index in range(77):
            decision = index * 900_000
            for symbol_index, symbol in enumerate(("BTCUSDT", "ETHUSDT")):
                target.write(
                    json.dumps(
                        {
                            "config_hash": "c" * 64,
                            "decision_time_ms": decision,
                            "label": labels[(index + symbol_index) % len(labels)],
                            "symbol": symbol,
                            "vertical_barrier_time_ms": decision + 3_600_000,
                        },
                        sort_keys=True,
                    )
                    + "\n"
                )
    return root
