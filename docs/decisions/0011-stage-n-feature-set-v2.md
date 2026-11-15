# ADR-0011 — Stage N numeric feature set v2

- Status: **ACCEPTED**
- Date: **16/11/2026**
- Scope: numeric feature formulas, point-in-time lineage, missing rules and optional context coverage

## Decision

Keep Stage I feature v1 immutable and introduce feature set `2.0.0` with 20 deterministic numeric
features. Calculate with Decimal, require closed records whose event and close times are strictly before
the decision, and record lineage for every input event. Fail closed on missing core inputs, invalid
market invariants, duplicate timestamps or unaligned basis.

Include mark/index basis after its 100% aligned observed-window audit. Exclude funding and open interest
despite 100% within-window completeness because their 1–2 day history fails the locked 30-day span
gate. Remove exact/redundant/non-stationary candidates before model training. Keep predictive ablation
for Stage O TRAIN/VALIDATION; never use FINAL_HOLDOUT for feature selection.

## Consequences

- A sample may be rejected instead of imputed when core market evidence is incomplete.
- Funding/OI cannot quietly enter a model until a new version and coverage evidence exist.
- Stage O must explicitly use v2 and fit all learned transforms on TRAIN only.
- Implementation uses existing local DuckDB/NumPy and creates no new dependency or cash cost.

Evidence: `docs/FEATURE_REGISTRY.md`, `tests/features/`, `reports/feature-ablation.md`.
