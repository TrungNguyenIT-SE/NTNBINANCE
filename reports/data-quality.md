# Stage F data-quality acceptance report

> Run date: `11/11/2026` (Asia/Saigon)
>
> Quality policy: `1.1.0`
>
> Schema: `1.0.0`
>
> Accepted run ID: `13f11d10018f9914`
>
> Result: **PASS — Gate A/Data**

## Acceptance summary

| Check | Result |
|---|---:|
| Raw records audited | 9,232 |
| Parsed candle observations | 8,650 |
| Clean base candles | 8,638 |
| Derived 15m + 1h candles | 708 |
| Quarantined observations | 12 |
| Duplicate observations | 0 |
| Source conflicts | 0 |
| Missing bars | 0 |
| Out-of-order arrivals | 0 |
| Clock-skew observations detected | 16 |
| Critical flags in clean output | **0** |
| Candle coverage groups below 99.9% | **0 / 36** |
| Funding/OI coverage groups below 99.9% | **0 / 6** |
| Native Binance comparison | **12 / 12 exact matches** |
| Idempotent rerun | **same run ID, `reused=true`** |

## Inputs and immutable identities

- Raw manifest SHA-256: `6B68057E9780A88E18B7A25737CF04D5309B7C03F9241A95D50339805B4BBA29`
- Clean manifest SHA-256: `CA988A80E7F4704272E317F35BD6DEE1D01695A541D3CEBEA9A6719684C3B13B`
- Published clean Parquet: 30 files, 982,349 bytes
- Published quarantine Parquet: 3 files, 9,455 bytes

Runtime data is Git-ignored; these hashes and the run ID bind this report to the audited local artifacts.

## Coverage by feature

All 36 candle groups split by dataset, symbol, interval and UTC date achieved 100% coverage over their observed first-to-last window. The groups cover:

- datasets: trade, mark price and index price;
- symbols: BTCUSDT and ETHUSDT;
- intervals: 1m, derived 15m and derived 1h;
- UTC dates: 09–10/11/2026.

Non-candle raw feature coverage also reached 100% over each observed daily window:

| Feature | Symbol | UTC date | Cadence | Actual / expected |
|---|---|---|---:|---:|
| Funding rate | BTCUSDT | 10/11/2026 | 8h | 3 / 3 |
| Funding rate | ETHUSDT | 10/11/2026 | 8h | 3 / 3 |
| Open interest | BTCUSDT | 09/11/2026 | 5m | 74 / 74 |
| Open interest | BTCUSDT | 10/11/2026 | 5m | 214 / 214 |
| Open interest | ETHUSDT | 09/11/2026 | 5m | 74 / 74 |
| Open interest | ETHUSDT | 10/11/2026 | 5m | 214 / 214 |

Coverage is intentionally measured only inside the captured window; it does not claim historical coverage before Stage E collection began.

## Quarantine and explicit exclusions

The 12 quarantined rows are REST observations of still-open candles. Each carries `INCOMPLETE_BAR` and `CLOCK_SKEW`; none entered clean output. No source value was repaired or imputed.

Resampling excluded 8 partial 15m buckets and 12 partial 1h buckets at capture-window boundaries. These are expected boundary exclusions, not internal missing bars. No incomplete output candle was published.

Four final WebSocket 1m candles carry non-critical `CLOCK_SKEW` because the source event clock was about 24 seconds ahead of the local ingestion clock. They remain visibly flagged. Stage H/N must exclude them from training windows unless a later evidence-backed clock policy explicitly admits them.

## Independent native-interval comparison

One deterministic sample was selected per dataset × symbol × target interval:

- 3 datasets × 2 symbols × 2 intervals = 12 samples;
- target intervals: 15m and 1h;
- all OHLC fields compared as exact decimals;
- trade klines additionally compared base/quote volume, trade count and taker-buy volumes;
- result: 12 matched, 0 mismatched.

The comparison queried Binance public USDⓈ-M endpoints and required no trading key or paid service.

## Automated verification

Full repository gate after Stage F:

```text
114 tests passed
statement + branch coverage: 91.09%
Ruff: pass
Ruff format: pass
mypy strict: pass
pip check: pass
frontend lint/format/typecheck/test/build: pass
```

Focused tests are under `tests/data_quality/` and cover parsing, invariants, non-destructive flags, reconciliation, gaps, ordering, clock skew, hand-calculated resampling, mixed/partial bucket rejection, Parquet publication, native comparison and idempotent reprocessing.

## Gate decision

Stage F passes because the clean publication contains no Critical quality error, every detected incomplete observation is quarantined, every partial resample bucket is deliberately excluded, all observed coverage groups exceed 99.9%, and the native Binance sample comparison is exact.

The project incurred **0 VNĐ in new cash cost**: DuckDB/Parquet and all verification run locally using open-source software, existing hardware and public Binance market-data endpoints.
