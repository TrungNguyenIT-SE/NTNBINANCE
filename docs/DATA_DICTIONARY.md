# Data Dictionary — NTN Binance

> Contract version: `1.0.0`
> Scope: Binance USDⓈ-M perpetual, `BTCUSDT` and `ETHUSDT`
> Canonical storage timezone: UTC
> Status: locked for Stage D

## 1. Conventions

- Names use `snake_case`; symbols/pairs and enum values use uppercase.
- Every timestamp is Arrow `timestamp[ms, tz=UTC]`. Source epochs are milliseconds.
- Prices, quantities, volumes and rates parse from source strings to `decimal128(38,18)`, never `float32`.
- Required identifiers/timestamps are not nullable. Optional source fields may be null only as documented.
- Every clean row requires `schema_version`, `source`, `source_endpoint`, `event_time`, `ingested_at`, `ingestion_batch_id`, `quality_flags`, and `raw_ref`.
- Trade, mark and index candles are separate datasets and never silently substitute for one another.

## 2. Common metadata

| Field | Logical type | Null | Meaning / rule |
|---|---|---:|---|
| `schema_version` | string | no | Semantic contract version; Stage D is `1.0.0`. |
| `venue` | enum | no | Always `BINANCE` in v1. |
| `market` | enum | no | Always `USD_M_PERPETUAL` in v1. |
| `source` | enum | no | `REST`, `WEBSOCKET`, or `DERIVED`. |
| `source_endpoint` | string | no | Endpoint/stream identifier without secrets or credentials. |
| `event_time` | timestamp UTC | no | Binance event time; dataset fallback is defined below. |
| `ingested_at` | timestamp UTC | no | Local UTC instant after the complete payload arrives. |
| `ingestion_batch_id` | UUID string | no | One immutable ingest/reconciliation attempt. |
| `quality_flags` | list&lt;enum&gt; | no | Empty means no detected issue; flags are not silently discarded. |
| `raw_ref` | string | no | Relative path plus record locator/hash to immutable raw payload. |

`event_time <= ingested_at` is mandatory. `ingested_at` is provenance, not market time.

## 3. Trade OHLCV candles — `candles`

Source: `/fapi/v1/klines` and USDⓈ-M kline stream. Binance identifies a kline by open time; the clean key adds market context.

**Unique key:** `(venue, market, symbol, interval, price_kind, open_time)`, with `price_kind=TRADE`.

| Field | Type | Null | Unit / meaning |
|---|---|---:|---|
| `symbol` | string | no | `BTCUSDT` or `ETHUSDT`. |
| `interval` | enum | no | MVP inference: `15m`, `1h`; base ingest may use `1m`/`5m`. |
| `price_kind` | enum | no | `TRADE`. |
| `open_time` | timestamp UTC | no | Inclusive start boundary. |
| `close_time` | timestamp UTC | no | `open_time + interval - 1 ms`, inclusive. |
| `open`, `high`, `low`, `close` | decimal | no | Trade prices, quote asset per base asset. |
| `volume_base` | decimal | no | Base-asset volume; non-negative. |
| `volume_quote` | decimal | no | Quote-asset volume; non-negative. |
| `trade_count` | int64 | no | Non-negative trade count. |
| `taker_buy_volume_base` | decimal | no | Taker-buy base volume. |
| `taker_buy_volume_quote` | decimal | no | Taker-buy quote volume. |
| `first_trade_id`, `last_trade_id` | int64 | yes | Stream-only trade IDs. |
| `is_closed` | boolean | no | Source/reconciliation finality. Only `true` enters features or prediction. |

REST klines have no event-time field, so `event_time := close_time`; `ingested_at` records when the row became locally knowable. WebSocket uses payload event time. An update with `is_closed=false` may exist only in raw/staging.

## 4. Mark-price candles — `mark_price_candles`

Source: `/fapi/v1/markPriceKlines`.

**Unique key:** `(venue, market, symbol, interval, price_kind, open_time)`, with `price_kind=MARK`.

Fields are common metadata plus `symbol`, `interval`, `open_time`, `close_time`, `open`, `high`, `low`, `close`, `is_closed`. Binance placeholder fields remain only in raw. Volume is not invented.

## 5. Index-price candles — `index_price_candles`

Source: `/fapi/v1/indexPriceKlines`.

**Unique key:** `(venue, market, pair, interval, price_kind, open_time)`, with `price_kind=INDEX`.

The identifier is `pair` because an index is not a tradable contract. Other fields match mark candles. MVP pairs are `BTCUSDT` and `ETHUSDT`.

## 6. Funding events — `funding_rates`

Source: `/fapi/v1/fundingRate`.

**Unique key:** `(venue, market, symbol, funding_time, rate_type)`.

| Field | Type | Null | Meaning |
|---|---|---:|---|
| `symbol` | string | no | Perpetual contract symbol. |
| `funding_time` | timestamp UTC | no | Effective funding time supplied by Binance. |
| `funding_rate` | decimal | no | Signed ratio, not percent. |
| `mark_price` | decimal | yes | Mark price associated with the funding charge. |
| `rate_type` | string | no | Explicit source value; documented migration default only for legacy rows. |
| `event_time` | timestamp UTC | no | Equal to `funding_time` for REST history. |

Realized funding is available only when `funding_time <= decision_time` and `ingested_at <= decision_time`. Future estimates are a separate dataset and cannot masquerade as history.

## 7. Open-interest periods — `open_interest`

Source: `/futures/data/openInterestHist`.

**Unique key:** `(venue, market, symbol, period, event_time)`.

| Field | Type | Null | Meaning |
|---|---|---:|---|
| `symbol` | string | no | Contract symbol. |
| `period` | enum | no | Binance aggregation period such as `5m`, `15m`, `1h`. |
| `event_time` | timestamp UTC | no | Binance `timestamp`, defined as period end. |
| `open_interest_base` | decimal | no | Source `sumOpenInterest`. |
| `open_interest_value` | decimal | no | Source `sumOpenInterestValue`. |
| `cmc_circulating_supply` | decimal | yes | Context only; excluded from the core model until approved. |

The endpoint has limited history, so raw observations are persisted. No forward-fill crosses a missing period unless a feature records age and missingness.

## 8. Instrument metadata — `instruments`

Source: `/fapi/v1/exchangeInfo`.

**Unique key:** `(venue, market, symbol, valid_from)`.

| Field | Type | Null | Meaning |
|---|---|---:|---|
| `symbol`, `pair` | string | no | Contract and underlying pair. |
| `contract_type`, `status` | string | no | Contract type and observed status. |
| `base_asset`, `quote_asset`, `margin_asset` | string | no | Asset identifiers. |
| `onboard_time` | timestamp UTC | no | Listing time. |
| `price_tick_size` | decimal | no | `PRICE_FILTER.tickSize`, not display precision. |
| `quantity_step_size`, `min_quantity` | decimal | no | `LOT_SIZE` rules. |
| `valid_from` | timestamp UTC | no | Inclusive start of local metadata validity. |
| `valid_to` | timestamp UTC | yes | Exclusive end; null means current. |

Metadata is slowly changing. Historical data joins the version valid at `decision_time`; current metadata is not retroactively applied without a migration.

## 9. Quality flags

Stable v1 values: `DUPLICATE_KEY`, `MISSING_BAR_BEFORE`, `OUT_OF_ORDER`, `CLOCK_SKEW`, `INVALID_OHLC`, `NEGATIVE_VOLUME`, `INCOMPLETE_BAR`, `SOURCE_CONFLICT`, `LATE_ARRIVAL`, `NULL_REQUIRED_FIELD`, `UNKNOWN_SCHEMA`.

- Critical/quarantine: invalid OHLC, negative volume, required null, unknown schema, unresolved source conflict.
- Prediction exclusion: every critical flag plus incomplete bar.
- Other flags are diagnostic for Stage F and are never silently repaired.

## 10. Official sources

- [Binance USDⓈ-M market-data API](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data)
- [Binance USDⓈ-M kline stream](https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/websocket-market-streams/Kline-Candlestick-Streams)

Sources rechecked 09/11/2026. Stage E must retain raw payloads and fail closed on unmapped fields because external APIs may change.
