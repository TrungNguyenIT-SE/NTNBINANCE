# Stage N feature stability and ablation report

- Date: 16/11/2026 (Asia/Saigon)
- Feature version: `2.0.0`
- Clean run: `13f11d10018f9914`
- Result: **PASS — feature set v2 locked**
- FINAL_HOLDOUT opened: **false**
- Incremental cash cost: **0 VNĐ**

## Audit population

The audit generated 152 point-in-time vectors for BTCUSDT and ETHUSDT from the immutable Stage F clean
run. It used every eligible decision timestamp after the 20×15m and 4×1h warm-up. It did not read label
outcomes and therefore measures calculability/stability, not predictive performance.

| Check | Result |
|---|---:|
| Final feature count | 20 |
| Eligible development vectors | 152 |
| Non-finite values | 0 |
| Zero-variance retained features | 0 |
| Median decision-to-latest-event lag | 1 ms |
| Maximum decision-to-latest-event lag | 1 ms |
| Future-isolation test | PASS for all 20 values |

## Coverage gate

| Dataset/context | Completeness | Span | Gate result |
|---|---:|---:|---|
| Mark/index basis | 100% | 2 days | INCLUDE |
| Funding | 100% | 1 day | EXCLUDE — below 30-day span |
| Open interest | 100% | 2 days | EXCLUDE — below 30-day span |

This distinguishes complete capture from sufficient history. Funding/OI remain available as raw
research sources but are not model inputs in v2.

## Candidate decisions

| Candidate | Decision | Reason |
|---|---|---|
| Raw price level | REMOVE | Non-stationary scale and symbol-price leakage risk |
| Quote-volume ratio | REMOVE | Redundant activity representation beside base-volume features |
| `taker_imbalance` | REMOVE | Exact affine duplicate of `taker_buy_ratio` (correlation 1.0) |
| Funding features | REMOVE FROM v2 | History-span gate failed |
| Open-interest features | REMOVE FROM v2 | History-span gate failed |
| Return/body geometry | RETAIN | Correlation 0.99993 in short capture, but distinct prior-close vs intrabar formulas |

No feature was selected because it improved validation or final-test metrics. Predictive value and
model-level ablation are deferred to Stage O with TRAIN/VALIDATION only.

## Missing-value policy verification

- Missing core history, volume, taker volume, trade count or exact basis alignment rejects the sample.
- Invalid OHLC, negative activity, taker volume above total volume and duplicate timestamps reject.
- A genuine observed zero denominator maps to neutral zero only for documented activity ratios.
- No future fill, cross-symbol fill, global mean fill or backward fill is performed.

## Reproduction

```powershell
.\.venv\Scripts\python.exe scripts/run-feature-ablation.py
.\.venv\Scripts\python.exe -m pytest tests/features -q
```

Machine-readable per-feature min/max/variance and correlations are stored in
`reports/feature-ablation.json`.
