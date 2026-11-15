"""Run Stage N coverage/stability ablation without opening the final holdout."""

from __future__ import annotations

import json
import math
import statistics
from pathlib import Path

import numpy as np

from ntnbinance.features.audit import development_feature_vectors
from ntnbinance.features.coverage import evaluate_coverage
from ntnbinance.features.models import CoverageEvidence
from ntnbinance.features.registry import FEATURE_NAMES, FEATURE_VERSION

ROOT = Path(__file__).resolve().parents[1]
CLEAN_ROOT = (
    ROOT / "data" / "clean" / "candles" / "schema_version=1.0.0" / "run_id=13f11d10018f9914"
)


def main() -> None:
    vectors = development_feature_vectors(CLEAN_ROOT)
    if not vectors:
        raise RuntimeError("no development feature vectors were produced")
    matrix = np.asarray([item.values for item in vectors], dtype=np.float64)
    stats = []
    for index, name in enumerate(FEATURE_NAMES):
        values = matrix[:, index]
        stats.append(
            {
                "feature": name,
                "finite": int(np.isfinite(values).sum()),
                "variance": float(np.var(values)),
                "minimum": float(np.min(values)),
                "maximum": float(np.max(values)),
            }
        )
    if not np.isfinite(matrix).all():
        raise RuntimeError("non-finite development feature detected")
    correlations = np.corrcoef(matrix, rowvar=False)
    high_pairs: list[dict[str, float | str]] = []
    for left in range(len(FEATURE_NAMES)):
        for right in range(left + 1, len(FEATURE_NAMES)):
            value = float(correlations[left, right])
            if math.isfinite(value) and abs(value) >= 0.98:
                high_pairs.append(
                    {
                        "left": FEATURE_NAMES[left],
                        "right": FEATURE_NAMES[right],
                        "correlation": value,
                    }
                )

    coverage = {
        "basis": evaluate_coverage(
            CoverageEvidence("mark/index basis", 380, 380, 2),
            minimum_percent=99.9,
            minimum_span_days=1,
        ),
        "funding": evaluate_coverage(
            CoverageEvidence("funding", 6, 6, 1),
            minimum_percent=99.0,
            minimum_span_days=30,
        ),
        "open_interest": evaluate_coverage(
            CoverageEvidence("open interest", 576, 576, 2),
            minimum_percent=99.0,
            minimum_span_days=30,
        ),
    }
    payload = {
        "feature_version": FEATURE_VERSION,
        "clean_run_id": "13f11d10018f9914",
        "samples": len(vectors),
        "symbols": sorted({item.symbol for item in vectors}),
        "maximum_lineage_lag_ms": max(
            item.decision_time_ms - item.max_event_time_ms for item in vectors
        ),
        "median_lineage_lag_ms": statistics.median(
            item.decision_time_ms - item.max_event_time_ms for item in vectors
        ),
        "feature_stats": stats,
        "high_correlation_pairs": high_pairs,
        "coverage": {
            name: {
                "decision": result.decision.value,
                "percentage": result.percentage,
                "span_days": result.span_days,
                "reason_codes": result.reason_codes,
            }
            for name, result in coverage.items()
        },
        "removed_candidates": {
            "raw_price_level": "non-stationary scale and symbol leakage",
            "quote_volume_ratio": "redundant with base-volume activity in v2 audit",
            "taker_imbalance": "exact affine duplicate of taker_buy_ratio",
            "funding_features": "history span below 30-day gate",
            "open_interest_features": "history span below 30-day gate",
        },
        "final_features": FEATURE_NAMES,
        "final_holdout_opened": False,
    }
    output = ROOT / "reports" / "feature-ablation.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "samples": payload["samples"],
                "features": len(FEATURE_NAMES),
                "non_finite": int((~np.isfinite(matrix)).sum()),
                "high_correlation_pairs": len(high_pairs),
                "coverage": payload["coverage"],
                "final_holdout_opened": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
