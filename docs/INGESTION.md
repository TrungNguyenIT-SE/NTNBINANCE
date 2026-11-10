# Binance USDⓈ-M Public Data Ingestion

> Stage E baseline: `1.0.0`
> Updated: `11/11/2026`
> Authentication: none; public market data only

## Dataset matrix

| Dataset | Endpoint | Resolution | MVP instruments | Pagination identity |
|---|---|---|---|---|
| Trade OHLCV | `/fapi/v1/klines` | 1m | BTCUSDT, ETHUSDT | open time |
| Mark-price candles | `/fapi/v1/markPriceKlines` | 1m | BTCUSDT, ETHUSDT | open time |
| Index-price candles | `/fapi/v1/indexPriceKlines` | 1m | BTCUSDT, ETHUSDT | open time |
| Realized funding | `/fapi/v1/fundingRate` | event | BTCUSDT, ETHUSDT | funding time + rate type |
| Open-interest history | `/futures/data/openInterestHist` | 5m | BTCUSDT, ETHUSDT | period-end timestamp |
| Closed trade klines | `/market/stream?...@kline_1m` | 1m live | BTCUSDT, ETHUSDT | open time |

The 1m base interval is locked by ADR-0002. Stage F resamples only closed 1m candles to 15m and 1h.

## Safety invariants

- REST base URL is exactly `https://fapi.binance.com`.
- WebSocket URL uses the post-migration routed `/market` path.
- Only approved public GET paths are accepted.
- `apiKey`, `signature`, `listenKey` and equivalent fields are rejected before request or persistence.
- Timeout is finite; retries are bounded to five attempts.
- Retryable cases are transport errors, 408, 418, 429 and selected 5xx responses.
- Backoff is exponential with jitter and honors `Retry-After` when present.
- `X-MBX-USED-WEIGHT-*` is parsed; the 1-minute limit is learned from `exchangeInfo`; ≥80% usage triggers proactive pacing.
- Response pages must advance monotonically. Non-advancing or malformed pages fail closed.
- WebSocket ping/pong is handled by the protocol client; reconnection uses bounded backoff and URL-based resubscription.
- Only final WebSocket klines (`x=true`) are persisted.

## Operations

### Backfill the standard 24-hour validation window

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ingest-backfill.ps1 `
  -Hours 24 `
  -DataRoot data/raw
```

The command uses Binance server time, not the workstation clock. The maximum accepted CLI window is 720 hours to prevent accidental unbounded downloads.

### Capture live closed klines

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ingest-stream.ps1 `
  -Minutes 2 `
  -Interval 1m `
  -DataRoot data/raw
```

Production-like local monitoring may use up to 1,440 minutes. Binance normally disconnects a connection after 24 hours; the client reconnects and the next final kline triggers sequence-gap recovery if needed.

### Audit raw storage

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ingest-audit.ps1 `
  -DataRoot data/raw
```

The audit verifies every manifest path stays within the raw root, every file exists, SHA-256 and row count match, record identities are unique, and the identity index equals all published records.

## Raw layout

```text
data/raw/
├── manifest.jsonl
├── identity-index.txt
└── {dataset}/
    └── ingest_date=YYYY-MM-DD/
        └── batch_id={uuid}/
            └── part-00000.jsonl.gz
```

Each record stores schema version, dataset, source, endpoint, sanitized public request parameters, stable record key, event time, `ingested_at`, exact payload, content hash and identity hash.

`identity_sha256 = SHA256(dataset + NUL + record_key + NUL + content_sha256)`

This makes identical reruns idempotent while retaining a source conflict whose payload changed for the same logical key.

## Recovery sequence

```text
stream disconnects
  → reconnect + URL resubscription
  → receive next closed kline
  → compare open_time with last closed watermark
  → if gap: REST backfill [expected_open, new_open - 1]
  → persist/deduplicate recovery batch
  → persist new stream event
  → advance watermark
```

Malformed payloads, failed recovery or manifest errors stop the affected operation. The pipeline never invents a candle or silently skips a detected gap.

## What Stage E does not do

- It does not clean, repair, resample or publish analytical Parquet.
- It does not assert ≥99.9% long-history coverage.
- It does not create features, labels, signals or orders.
- It does not use current account, position, order or user-data endpoints.

Those boundaries prevent Stage E evidence from being mistaken for the Stage F data-quality gate.
