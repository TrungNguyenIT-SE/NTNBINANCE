# ADR-0006 — Stage I baseline and selection policy

- Status: **ACCEPTED**
- Date: **13/11/2026**
- Scope: Stage I numeric baselines only

## Context

The project needs a reproducible floor before vision or sequence work. The locked Stage H split has
90 TRAIN and 26 VALIDATION samples; FINAL_HOLDOUT has 26 samples and cannot open before Stage W.
This dataset is mechanically valid but statistically small.

## Decision

1. Run majority, seeded random and always-no-trade floors.
2. Run a fixed rule using closed 1H trend, 15m trigger and ATR filter.
3. Run multinomial Logistic Regression after a TRAIN-only standard scaler.
4. Run `xgboost-cpu` locally with one worker and a fixed seed; GPU/cloud are not required.
5. Report accuracy, macro precision/recall/F1, every class, multiclass Brier, ECE-10 and the same
   Stage G net-cost comparator for every baseline.
6. Select the technical baseline by `(macro F1, accuracy, lower Brier)` among rule/logistic/XGBoost.
   Random/majority/no-trade are diagnostic floors and cannot become a deployable champion.
7. A future candidate must beat the locked primary baseline without materially worsening calibration
   or net-cost behavior. No baseline is authorized for live trading.

## Result and consequences

`xgboost_cpu` is the primary technical baseline (macro F1 `0.4607`, accuracy `0.4615`, ECE-10
`0.1507`). Its validation net-return sum after modeled costs is `-0.029636`; all directional
baselines are negative. The seeded random realization scores a higher macro F1 (`0.4966`) by chance
on 26 samples and is fully disclosed. Stage I therefore establishes a comparison bar but no trading
edge, production readiness or permission to open FINAL_HOLDOUT.

All packages and execution are local/open source. New cash cost is **0 VNĐ**. The complete evidence is
in `reports/baseline-v1.md` and `models/baselines/baseline-v1.json`.
