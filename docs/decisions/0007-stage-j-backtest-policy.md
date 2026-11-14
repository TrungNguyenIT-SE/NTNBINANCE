# ADR-0007 — Stage J execution-aware backtest policy

- Status: **ACCEPTED**
- Date: **15/11/2026**
- Scope: VALIDATION backtest for the locked Stage I XGBoost baseline

## Decision

Use a deterministic 1m event engine with delayed entry, adverse tick-rounded market fills, taker
fees, spread, slippage, realized funding, IOC participation-capped partial fills, exchange quantity
and notional constraints, conservative same-minute stop ordering and vertical expiry.

The engine reads membership/features/market data but no outcome label. FINAL_HOLDOUT remains sealed.
Cost sensitivity must be monotonic; latency sensitivity must alter at least one event timeline.

## Consequences

- Base validation: 20 filled trades, net PnL `-2.5634 USDT`, expectancy `-0.1282 USDT`, PF `0.3576`.
- Cost x1.5: `-3.7460 USDT`; cost x2: `-4.9749 USDT`.
- Mechanical/no-lookahead gate passes, but trading edge is **NO-GO**.
- Current exchange filters are used because historical metadata was not persisted; this limitation is
  explicit and blocks claims of tick-perfect historical execution.
- All processing remains local and adds **0 VNĐ** cash cost.

The detailed contract is `docs/BACKTEST_SPEC.md`; evidence is
`reports/backtest-validation.md`, `models/backtests/backtest-v1.json` and `tests/backtest/`.
