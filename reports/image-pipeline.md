# Stage M image-pipeline acceptance report

- Date: 16/11/2026
- Policy/config: `image-pipeline-v1`
- Exit gate: **PASS**
- Incremental cash cost: **0 VNĐ**

## Delivered controls

The implementation detects/crops chart ROI, preserves aspect ratio, measures explainable local quality,
reads four identity/time/price fields with pinned local OCR, and cross-checks them against user metadata
plus authoritative market price. It returns fail-safe `REJECTED_INPUT` or `NO_TRADE` for non-chart,
low-quality, mismatch, stale, incomplete-OCR and OOD cases.

Synthetic fixtures use only closed point-in-time OHLCV. TRAIN-only augmentation is deterministic by
seed and cannot flip/reverse time. OCR assets are checksum-verified at runtime.

## Locked benchmark matrix

The reproducible matrix has 27 cases: 3 themes × 3 resolutions × 3 source layouts. It was generated
after locking thresholds, without tuning against a final model test set.

| Metric | Result |
|---|---:|
| Quality accepted | 27 / 27 |
| OCR four fields correct | 27 / 27 |
| Median CPU latency | 1837.75 ms / image |
| p95 CPU latency | 4598.94 ms / image |
| Maximum CPU latency | 4715.45 ms / image |

Environment: Windows 11, Python 3.14.2. Per-case values are in
`reports/image-pipeline-benchmark.json`.

## Negative/golden gates

- Non-chart and severely blurred images are rejected before OCR.
- Declared/OCR symbol mismatch is rejected.
- Missing header evidence, stale pair, price mismatch and unknown source abstain with `NO_TRADE`.
- Renderer rejects unsorted/future candles and unsupported scope.
- OCR parser never fuzzy-corrects an unknown symbol or timeframe.
- Model checksum tampering fails closed.

The two Binance screenshots supplied in the request were visual layout references only. They are not
stored as immutable fixtures, so this report does not claim measured accuracy on those attachments. A
future real-world holdout must be consented, versioned and kept sealed.

## Evidence

- Tests: `tests/image_pipeline/`
- Configuration: `configs/images/image-pipeline-v1.toml`
- Benchmark: `scripts/benchmark-image-pipeline.py`
- Contract: `docs/IMAGE_PIPELINE.md`
- Decision: `docs/decisions/0010-stage-m-image-pipeline-policy.md`
- Dependency audit: `reports/stage-m-license-audit.md`
- Clean-checkout verification: `reports/stage-m-clean-checkout.md`

Conclusion: mismatch, stale and non-chart paths are caught under locked v1 thresholds; Stage M may
close and Stage N may begin.
