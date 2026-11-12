# Stage H split audit

> Audit date: `13/11/2026` (Asia/Saigon)
>
> Split: `v1 / engine 1.0.0`
>
> Result: **PASS — final holdout remains sealed**

## Artifact identity

| Artifact | SHA-256 / ID |
|---|---|
| Source label run | `8780c5a42857c830` |
| Source label JSONL | `ca156100916c3d4d32e17711c5f25697317de8aeb900865da8f0d65852666e55` |
| Source label manifest | `ad360f7a0cbe983d22bff5889638648c9435a7037b890bb24a2649cd4f47c0af` |
| Split config canonical hash | `c4d8d299c1ad57ef7b9d00fa4d8496c88b86dce6d9638e04ffd237cc583fe27e` |
| Split manifest | `2d7a0a201d371418d2282db85c82dfa28ebb52e9a21e7548560c015e1922a0b2` |
| Final-holdout membership | `83606d4e4c905949e3b753e7df80dc51099c23dabf8922a7f5590d6a4cdf9528` |

## Primary partition audit

| Partition | Samples | First decision UTC | Last decision UTC |
|---|---:|---|---|
| TRAIN | 90 | 09/11 21:45 | 10/11 08:45 |
| PURGED_TRAIN_VALIDATION | 6 | 10/11 09:00 | 10/11 09:30 |
| VALIDATION | 26 | 10/11 09:45 | 10/11 12:45 |
| EMBARGO_VALIDATION_TEST | 6 | 10/11 13:00 | 10/11 13:30 |
| FINAL_HOLDOUT | 26 | 10/11 13:45 | 10/11 16:45 |

- Unique decision timestamps: 77.
- Symbols present together at every timestamp: BTCUSDT and ETHUSDT.
- Train→validation decision gap: 3,600,000 ms.
- Validation→holdout decision gap: 3,600,000 ms.
- Required embargo: 3,600,000 ms.
- Cross-partition label-window overlaps: 0.
- Duplicate sample IDs: 0.
- Assignment records containing a `label` field: 0.

## Walk-forward folds

| Fold | Train | Purged | Validation |
|---|---:|---:|---:|
| 1 | 38 | 6 | 26 |
| 2 | 64 | 6 | 26 |
| 3 | 90 | 6 | 26 |

## Development-only class audit

| Partition | LONG | SHORT | NO_TRADE | Total |
|---|---:|---:|---:|---:|
| TRAIN | 31 | 41 | 18 | 90 |
| VALIDATION | 6 | 13 | 7 | 26 |

The final-holdout class distribution was intentionally not computed or reported.

## Holdout state and authorization

```text
status: SEALED
opened: false
first permitted stage: W
authorized role: PROJECT_OWNER
```

The automated guard requires a one-time Stage W decision plus locked feature, model, calibration, risk-policy and code hashes. No unlock record exists in Stage H.

## Automated checks

`tests/leakage/` validates boundary counts, half-open overlap logic, exact embargo, chronological folds, symbol grouping, fit scopes, augmentation inheritance, malformed datasets, holdout authorization and manifest idempotency.

## Limitation

This split is mechanically valid but statistically small. The final holdout contains only 26 samples over 13 timestamps. It must not be used to claim production readiness; future data requires a new split version without modifying v1.

All split processing is local. New cash cost remains **0 VNĐ**.

## Repository quality gate

```text
138 tests passed
statement + branch coverage: 91.21%
Ruff lint/format: pass
mypy strict: pass
pip check: pass
frontend lint/format/typecheck/test/build: pass
```

The committed manifest checksum, packaged split CLI and the same quality gate passed in a detached clean worktree; see [`stage-h-clean-checkout.md`](stage-h-clean-checkout.md).
