# ADR-0004 — Stage G triple-barrier label policy

- Status: `ACCEPTED`
- Date: `13/11/2026`
- Config: `configs/labels/triple-barrier-v1.toml`
- Engine: `1.0.1`

## Context

The model must predict an economically meaningful direction, not merely the sign of a future close. Labels must be reproducible, cost-aware, point-in-time correct and robust to ambiguous OHLC paths.

## Decision

- Use final trade-price 15m candles and simple ATR(14).
- Place symmetric barriers at ±1 ATR from the decision close.
- Use four future 15m bars as the primary vertical horizon.
- Use the complete 1m sequence to resolve barrier order.
- Assign `NO_TRADE` when both barriers occur in the same 1m bar, required data is unsafe, no barrier occurs or modeled costs remove the edge.
- Model taker fees, spread, slippage, latency and realized funding through an immutable config.
- Hash the clean manifest, canonical config and engine version into the label run ID.

## Consequences

- The same inputs and config always produce identical labels.
- No inference about intrabar path is made when 1m OHLC is still ambiguous.
- The short Stage F data window can audit mechanics and class balance but cannot validate market edge.
- Stage H must split by time before any alternative label parameters are evaluated.
- Stage J remains responsible for richer fill, tick/step, partial-fill and liquidation simulation.

## Rejected alternatives

- Future-close sign: ignores path, volatility and costs.
- Random dual-touch ordering: non-deterministic and optimistic.
- Always upper-first/lower-first: embeds unobservable OHLC ordering bias.
- Hard-coded current account fee: changes by tier and over time.
- Optimizing parameters on the final holdout: creates selection leakage.
