# Backtest specification v1

> Stage: J
>
> Status: `LOCKED`
> Scope: BTCUSDT and ETHUSDT USDⓈ-M perpetual, VALIDATION only

## 1. Purpose and safety boundary

This engine evaluates the locked Stage I `xgboost_cpu` policy under explicit execution assumptions.
It is research/paper simulation only: no API key, account, order endpoint, leverage or real capital is
used. FINAL_HOLDOUT remains sealed until Stage W, and Stage J never opens the label JSONL. It rebuilds
VALIDATION inputs from the label-blind split manifest and point-in-time clean candles.

The backtest validates mechanics and comparative sensitivity. It cannot establish production
readiness from 26 samples over 13 timestamps.

## 2. Event timeline

```text
closed 15m/1H inputs
        ↓
decision_time
        ↓ configured latency
order_arrival_time
        ↓ ceil to the next observable 1m opening event
entry fill / partial fill / cancel
        ↓ manage only candles at or after entry
take-profit / stop-loss / vertical exit
        ↓
fee + spread/slippage + realized funding → net PnL
```

- A signal never fills at the decision candle close.
- Base latency is 1,000 ms. With 1m data, the first usable price event is the next minute open at or
  after arrival; this deliberately avoids pretending to know the price one second inside a candle.
- Management uses no candle before entry and stops reading at the selected exit.
- The vertical barrier is 3,600,000 ms after decision.
- If stop and take are both inside one 1m candle, `STOP_FIRST` is used.

## 3. Fill model

Signals are simulated as aggressive IOC orders:

1. Raw entry is the first eligible 1m open.
2. Half-spread and slippage move price adversely.
3. Buy prices round up and sell prices round down to `PRICE_FILTER.tickSize`.
4. Requested quantity is `floor(100 USDT / fill_price, MARKET_LOT_SIZE.stepSize)`.
5. Quantity must meet min/max quantity and minimum notional.
6. Available quantity is capped at `0.1%` of the entry candle base volume.
7. If available quantity is below requested quantity but remains valid, the order is
   `PARTIALLY_FILLED`; the IOC remainder is cancelled. Invalid residual fills are `UNFILLED`.

Exit fills apply the same adverse spread/slippage and tick rounding. The test suite includes full,
partial and unfilled cases even though all 20 directional validation signals were fully filled.

## 4. Costs and PnL

For filled quantity `q`, direction `d` (`+1` long, `-1` short):

```text
gross_pnl = d × (raw_exit - raw_entry) × q
execution_price_pnl = d × (exit_fill - entry_fill) × q
fees = fee_rate × q × (entry_fill + exit_fill)
funding = d × sum(realized_rates crossed while held) × entry_fill × q
net_pnl = execution_price_pnl - fees - funding
```

The configured taker fee is 5 bps per side, half-spread 0.5 bps per side and slippage 1 bp per side.
Funding includes only `entry_time < funding_time <= exit_time`. Positive funding is a long cost and a
short receipt. Cost stress multiplies fee/spread/slippage by 1, 1.5 and 2; it does not multiply market
movement or funding.

## 5. Instrument rules snapshot

Stage E used `/exchangeInfo` for rate limits but did not persist versioned instrument metadata. Stage
J therefore locks the current public snapshot in `data/manifests/exchange-info-stage-j.json` and
explicitly sets `historical_at_decision_time=false`.

| Symbol | Tick | Market step/min qty | Max market qty | Min notional |
|---|---:|---:|---:|---:|
| BTCUSDT | 0.10 | 0.001 | 120 | 50 USDT |
| ETHUSDT | 0.01 | 0.001 | 2,000 | 20 USDT |

This is a documented approximation, not a retroactive claim that the rules were identical at every
historical decision. Future ingestion must persist slowly-changing metadata with validity intervals.

## 6. Metrics and segmentation

The report includes gross/net PnL, expectancy, profit factor, drawdown, win rate, annualized Sharpe
and Sortino, fill outcomes, cost decomposition and exit reasons. Sharpe/Sortino aggregate PnL by
15m decision timestamp against 10,000 USDT starting equity and use 35,040 periods/year. With only 13
periods these are diagnostics, not evidence.

Required slices are symbol, side, UTC month, point-in-time ATR regime and confidence bucket. Empty or
tiny segments remain visible rather than being suppressed.

## 7. Known exclusions

- No order-book depth, queue position or sub-minute path reconstruction.
- No maker orders, liquidation, leverage, margin calls, ADL or portfolio margin.
- No live order placement and no claim that candle-volume participation equals real fillability.
- Independent 100 USDT trades; overlapping positions are not capital-netted in v1.
- Current exchange filters substitute for missing historical instrument metadata.

Any semantic change requires a new config/engine version and a new immutable report.
