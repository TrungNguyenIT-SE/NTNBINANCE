# Stage I baseline v1 report

> Evaluation date: `13/11/2026` (Asia/Saigon)
>
> Result: **PASS — reproducible development baseline; final holdout remains sealed**

## Locked identity

- Run ID: `f9134abdb58bc0d4`
- Config hash: `0cd86442979f5b720242ae187a14ef79add65b05e338750c014d7db3f8f80961`
- Split SHA-256: `2d7a0a201d371418d2282db85c82dfa28ebb52e9a21e7548560c015e1922a0b2`
- Label JSONL SHA-256: `ca156100916c3d4d32e17711c5f25697317de8aeb900865da8f0d65852666e55`
- Cost config hash: `35b4571aaa7280290d1e996f7e4aebe9e290db3ab82f6f2c9145cf772f4d6f16`
- Artifact SHA-256: `8c56c1b6a80fb1a5edf22185a337fbfe9967cc00d2b0fdc08035951771e4cbcf`
- Seed: `20261113`
- Samples: TRAIN `90`, VALIDATION `26`, FINAL_HOLDOUT skipped `26`.
- Holdout labels read: `0`; opened: `false`.

## Validation results (all required metrics)

| Baseline | Accuracy | Macro F1 | Macro precision | Macro recall | Brier | ECE-10 | Trades | Net return sum | Max DD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| majority | 0.5000 | 0.2222 | 0.1667 | 0.3333 | 0.6440 | 0.0444 | 26 | -0.017355 | 0.032815 |
| random | 0.5000 | 0.4966 | 0.5333 | 0.5189 | 1.0000 | 0.5000 | 21 | -0.008634 | 0.013472 |
| always_no_trade | 0.2692 | 0.1414 | 0.0897 | 0.3333 | 1.4615 | 0.7308 | 0 | 0.000000 | 0.000000 |
| rule_trend_trigger_atr | 0.3462 | 0.2638 | 0.2302 | 0.3187 | 1.3077 | 0.6538 | 14 | -0.029871 | 0.040018 |
| logistic_regression | 0.2692 | 0.2409 | 0.1895 | 0.3651 | 1.0429 | 0.4939 | 17 | -0.040066 | 0.043730 |
| xgboost_cpu | 0.4615 | 0.4607 | 0.4861 | 0.4933 | 0.7260 | 0.1507 | 20 | -0.029636 | 0.033101 |

## Per-class precision / recall / F1 / support

### majority

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| LONG | 0.0000 | 0.0000 | 0.0000 | 6 |
| SHORT | 0.5000 | 1.0000 | 0.6667 | 13 |
| NO_TRADE | 0.0000 | 0.0000 | 0.0000 | 7 |

### random

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| LONG | 0.3333 | 0.6667 | 0.4444 | 6 |
| SHORT | 0.6667 | 0.4615 | 0.5455 | 13 |
| NO_TRADE | 0.6000 | 0.4286 | 0.5000 | 7 |

### always_no_trade

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| LONG | 0.0000 | 0.0000 | 0.0000 | 6 |
| SHORT | 0.0000 | 0.0000 | 0.0000 | 13 |
| NO_TRADE | 0.2692 | 1.0000 | 0.4242 | 7 |

### rule_trend_trigger_atr

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| LONG | 0.0000 | 0.0000 | 0.0000 | 6 |
| SHORT | 0.3571 | 0.3846 | 0.3704 | 13 |
| NO_TRADE | 0.3333 | 0.5714 | 0.4211 | 7 |

### logistic_regression

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| LONG | 0.2353 | 0.6667 | 0.3478 | 6 |
| SHORT | 0.0000 | 0.0000 | 0.0000 | 13 |
| NO_TRADE | 0.3333 | 0.4286 | 0.3750 | 7 |

### xgboost_cpu

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| LONG | 0.3333 | 0.6667 | 0.4444 | 6 |
| SHORT | 0.6250 | 0.3846 | 0.4762 | 13 |
| NO_TRADE | 0.5000 | 0.4286 | 0.4615 | 7 |

## Decision

Primary Stage I baseline: **`xgboost_cpu`**. A later model must beat its locked validation macro F1 without materially worsening calibration or net-cost behavior. Selection used the predeclared tuple `macro F1 → accuracy → lower Brier`; random/majority/no-trade were floors, not eligible champions.

The seeded random draw happened to score macro F1 `0.4966` on only 26 samples, above XGBoost's `0.4607`; this is reported, not hidden. It is not a learnable or deployable policy and is highly unstable at this sample size. Every directional baseline had negative net return after costs; Stage I therefore demonstrates **no trading edge and authorizes no promotion or live trading**.

## Feature and fit boundary

All 13 numeric features are computed from candles with `close_time < decision_time`. They cover 15m returns/range/body/volume/taker flow, closed 1H trend, ATR and volatility, mark/index basis and symbol identity. StandardScaler and both learned models fit TRAIN only; VALIDATION is evaluation/selection only. Definitions and missing-data rules are locked in `docs/FEATURE_REGISTRY.md`.

## Backtest boundary

Returns use the Stage G entry reference, two-sided taker fee, half-spread, slippage, latency and funding sign. Barrier exits use the recorded first event; vertical exits use the closed 15m price; ambiguous 1m touches take the adverse barrier. This is a baseline comparator, not the full execution simulator required by Stage J (partial fills/tick/step/latency stress remain).

## Reproduction

```powershell
powershell -File scripts/run-baselines.ps1
```

The script regenerates the report and JSON artifact deterministically from the locked config, split, clean run and label run. All computation is local with open-source packages; new cash cost remains **0 VNĐ**. The 26-sample validation window is too small for production claims.

## Repository quality gate

```text
148 tests passed
statement + branch coverage: 91.08%
Ruff lint/format: pass
mypy strict: pass
pip check: pass
frontend lint/format/typecheck/test/build: pass
```

Clean-checkout setup, packaging, checksum and quality verification are recorded in `reports/stage-i-clean-checkout.md`.
