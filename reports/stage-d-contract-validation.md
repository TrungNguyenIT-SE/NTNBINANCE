# Stage D — Data Contract Validation

Date: 09/11/2026
Contract: `1.0.0`
Result: PASS

## Scope accepted

- Data dictionary covers trade OHLCV, mark/index candles, realized funding, open-interest periods and versioned instrument metadata.
- All stored timestamps are explicit UTC; UI timezone is presentation only.
- `open_time`, `close_time`, `event_time`, `ingested_at`, `decision_time` and `funding_time` have distinct meanings.
- Candle use is fail-closed: `is_closed=true` and `available_at <= decision_time` are both mandatory.
- Unique keys, schema version and stable quality flags are defined.
- Raw/clean/feature layout uses local Parquet + DuckDB and immutable lineage.
- Retention covers market data, images, derivatives, logs, temporary jobs and model artifacts without a paid service.

## Automated evidence

Focused contract suite:

```text
22 passed
```

Full repository quality gate:

```text
Ruff lint/format: PASS
mypy strict: PASS
pip check: PASS
pytest: 38 passed
statement/branch coverage: 100%
frontend lint/format/typecheck: PASS
Vitest: 5 passed
Vite production build: PASS
```

The suite explicitly rejects naive/non-UTC timestamps, wrong interval boundaries, open candles, data ingested after a decision, future event times, duplicate keys and unsupported schema versions.

## Official source review

Binance USDⓈ-M official market-data documentation was rechecked on 09/11/2026. It confirms that klines are identified by open time, funding history carries a funding timestamp, and open-interest history uses a period-end timestamp. Stage E must still preserve raw payloads because external schemas can change.

- https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data
- https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/websocket-market-streams/Kline-Candlestick-Streams

## Exit Gate D

PASS — timestamp semantics are unambiguous and executable tests prevent an unclosed or not-yet-available candle from entering a prediction.
