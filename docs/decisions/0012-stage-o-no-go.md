# ADR-0012 — Stage O NO-GO and no champion promotion

- Status: **ACCEPTED**
- Date: **16/11/2026**
- Scope: Stage O model selection, validation use and progression to Stage P

## Decision

Record Stage O as **NO-GO and incomplete**. Do not publish a champion and do not begin Stage P.
The locked Stage I macro-F1 baseline is `0.4607`, and Stage O requires at least `0.4707`.
The best resource-eligible result was the validation-selected numeric-v1 XGBoost diagnostic at
`0.4586`; it did not beat the baseline. Every evaluated candidate also produced negative
cost-aware net return on the 26-row validation partition.

Keep all 26 FINAL_HOLDOUT rows sealed. Stop model-family searching on the current validation set,
because the bounded sensitivity analysis already makes its selected scores optimistic. A new Stage O
attempt requires more independent historical TRAIN/VALIDATION evidence and a versioned real-chart
corpus. The current synthetic image benchmark is pipeline evidence, not evidence of generalization to
user screenshots.

## Consequences

- `models/candidates/champion-v1.joblib` is intentionally absent.
- Overall project progress remains `14/26`; the two final Stage O checklist items stay unchecked.
- Numeric, image-only and fusion implementations remain reproducible research candidates only.
- No calibration, live inference, auto-trading or financial recommendation is authorized.
- FINAL_HOLDOUT labels remain unread (`0`), preserving the later unbiased evaluation gate.
- All work used local CPU and open-source dependencies; new cash cost remains **0 VNĐ**.

Evidence: `reports/model-selection.md`, `models/candidates/model-selection-v1.json`,
`configs/models/model-selection-v1.toml`, `tests/model_selection/`.
