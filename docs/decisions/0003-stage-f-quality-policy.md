# ADR-0003 — Stage F clean-data and resampling policy

- Status: `ACCEPTED`
- Date: `11/11/2026`
- Decision owners: project owner and implementation audit

## Context

Stage E preserves source observations, including temporary open candles and WebSocket timing anomalies. Training directly from raw data would allow incomplete, conflicting or gap-affected windows into later stages. The project also requires a zero-new-cash-cost local stack.

## Decision

Use a deterministic Python quality pipeline with embedded DuckDB 2.0.0 to publish partitioned Parquet/ZSTD locally. The run ID is derived from the raw manifest plus schema and quality-policy versions.

- Source values are never silently corrected.
- Critical records and unresolved source conflicts are quarantined.
- Duplicate-equivalent observations select one deterministic representative.
- Non-critical timing/sequence conditions remain explicitly flagged.
- Only complete UTC-aligned closed buckets are resampled.
- Atomic directory publication and manifest reuse provide idempotent reprocessing.
- Funding/OI coverage is audited but those features are not promoted to clean training inputs in Stage F.

## Consequences

- Later stages can reproduce the exact clean run from its raw manifest and policy version.
- Boundary-partial buckets are intentionally absent; this is recorded as exclusion, not imputed data.
- A downstream split/feature builder must reject disallowed flags, especially `CLOCK_SKEW` and `MISSING_BAR_BEFORE`.
- DuckDB is an in-process MIT-licensed dependency and creates no server, account or fee.
- Local disk, CPU and existing Internet remain the only operating resources.

## Rejected alternatives

- Pandas-only mutable files: weaker atomic publication and query verification.
- Managed warehouse/object storage: violates the zero-new-cash-cost and local-first boundary.
- Forward fill/interpolation: invents market observations and hides gaps.
- Resampling partial buckets: creates misleading OHLCV and training leakage risk.
