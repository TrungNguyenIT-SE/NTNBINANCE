# Stage F data-quality pipeline

> Version: `1.1.0`
>
> Status: accepted
>
> Storage: local DuckDB + partitioned Parquet/ZSTD
>
> New cash cost: `0 VNĐ`

## Purpose and boundary

Stage F converts the immutable Stage E raw store into an auditable clean candle layer. It does not create labels, features or training splits. Every output run is content-addressed by the raw manifest, quality-policy version and schema version.

The accepted candle sources are `trade_klines`, `mark_price_klines` and `index_price_klines`. Funding rate and open interest remain immutable raw observations in this stage; their symbol/day coverage is reported so Stage N can decide whether they are admissible as point-in-time features.

## Deterministic flow

1. Audit every raw batch hash and the raw identity index before reading records.
2. Parse source fields without rounding, forward filling or rewriting values.
3. Attach quality flags for invalid OHLC, invalid/negative volume, incomplete bars, clock skew and arrival-order regressions.
4. Reconcile by `(dataset, symbol, interval, open_time)`.
5. Quarantine malformed, critical or conflicting observations.
6. Mark missing predecessors on retained rows.
7. Resample only complete, closed 1m or 5m UTC buckets into 15m and 1h.
8. Publish Parquet to a temporary directory, verify row counts, then rename atomically.
9. Reuse an already published run when the same run ID is requested again.

## Invariants and disposition

| Condition | Flag | Disposition |
|---|---|---|
| non-positive price or invalid OHLC ordering | `INVALID_OHLC` | quarantine |
| negative volume or trade count | `NEGATIVE_VOLUME` | quarantine |
| taker-buy volume exceeds total volume | `INVALID_VOLUME` | quarantine |
| candle is not final | `INCOMPLETE_BAR` | quarantine |
| unsupported schema/interval | `UNKNOWN_SCHEMA` | quarantine |
| valid final payloads disagree | `SOURCE_CONFLICT` | quarantine every conflicting candidate |
| identical logical candidates | `DUPLICATE_KEY` | retain one deterministic candidate with flag |
| missing predecessor | `MISSING_BAR_BEFORE` | retain with flag; incomplete resample bucket is excluded |
| arrival time regresses | `OUT_OF_ORDER` | retain with flag for explicit downstream filtering |
| event clock is more than 5 seconds ahead of ingestion clock | `CLOCK_SKEW` | retain with flag; downstream training must filter or explicitly justify |

No rule silently changes source OHLCV. Critical flags are prohibited from the published clean layer.

## Resampling contract

- UTC buckets are aligned by integer epoch boundaries.
- A 15m bucket requires exactly 15 × 1m bars or 3 × 5m bars.
- A 1h bucket requires exactly 60 × 1m bars or 12 × 5m bars.
- Base intervals may not be mixed inside one output bucket.
- Open is the first open; high/low are extrema; close is the final close.
- Volume and trade fields are summed only when the source dataset provides them.
- Any missing, open, duplicate-time or boundary-partial bucket is excluded.
- Derived rows retain a SHA-256 lineage identity over every source observation.

## Running and verifying

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\data-quality.ps1
```

Optional live comparison against Binance native interval candles:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\data-quality.ps1 `
  --compare-binance --comparison-samples 1
```

The live comparison uses only public market-data endpoints. It requires no API key, paid API or external service subscription. A mismatch exits non-zero.

Local runtime outputs under `data/clean/` and `data/quarantine/` are intentionally Git-ignored. The committed acceptance evidence is [`reports/data-quality.md`](../reports/data-quality.md).
