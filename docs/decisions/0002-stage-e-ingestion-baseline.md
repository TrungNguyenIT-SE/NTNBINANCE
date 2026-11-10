# ADR-0002 — Stage E ingestion baseline

- Status: `ACCEPTED`
- Date: `11/11/2026`
- Scope: Binance USDⓈ-M public market data for the MVP

## Context

The downstream 15m/1h feature pipeline needs one consistent base resolution, enough intrabar detail for later label analysis, point-in-time provenance, and recovery after WebSocket gaps. The project may not require a paid key, hosted broker, cloud queue or external data vendor.

Binance migrated regular USDⓈ-M market streams, including klines, to the routed `/market` WebSocket path. The connection has a 24-hour lifetime, so reconnect and resubscription are normal operating events.

## Decision

1. Use **1m** as the MVP base OHLCV resolution for `BTCUSDT` and `ETHUSDT`.
2. Collect trade, mark-price and index-price 1m candles.
3. Collect realized funding and 5m open-interest history as derivative context.
4. Use only public REST endpoints at `https://fapi.binance.com`; no API key or signed request is permitted.
5. Use `wss://fstream.binance.com/market/stream` combined kline subscriptions.
6. Persist exact responses as immutable gzip JSONL batches with record identity, event time, ingest time, source endpoint, request parameters and SHA-256 manifest.
7. Treat equal key + equal payload as idempotent duplicate; preserve equal key + changed payload in raw for later conflict resolution.
8. After stream reconnect, detect closed-kline sequence gaps and recover the missing range through REST before advancing the watermark.

## Why 1m instead of 5m

- Deterministically resamples to both 15m and 1h.
- Gives finer evidence when both label barriers appear touched inside one 15m candle.
- The two-symbol MVP remains within the existing local disk/CPU budget.
- Binance public endpoints provide it without a new monetary cost.

If resource pressure exceeds the Stage B limits, a later ADR may downgrade the base interval to 5m; existing 1m raw data remains immutable.

## Consequences

- More local storage and requests than 5m, controlled through bounded windows, manifest audit and the 80% disk pause policy.
- OI is natively collected at 5m and joined point-in-time later; it is not fabricated at 1m.
- Raw storage is not yet clean analytical Parquet. Conversion, OHLC validation and resampling belong to Stage F.
- The pipeline remains research-only and cannot place orders.

## Official references

- https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data
- https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/general-info
- https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/websocket-market-streams/Important-WebSocket-Change-Notice
