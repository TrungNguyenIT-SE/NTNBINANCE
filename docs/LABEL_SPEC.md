# Label specification — triple-barrier v1

> Specification version: `1.0.0`
>
> Engine version: `1.0.1`
>
> Status: locked for Stage G
>
> Primary horizon: 4 × 15m = 60 minutes

## 1. Objective and non-goals

This specification creates deterministic `LONG`, `SHORT` and `NO_TRADE` research labels for BTCUSDT and ETHUSDT USDⓈ-M perpetual futures. It does not place an order, claim profitability or choose a model. Labels measure whether a volatility-scaled directional barrier was reached first and still had positive modeled edge after explicit costs.

Stage G uses trade-price candles because they represent executable market prints. Mark/index candles remain context features for later stages and are not substituted into the target after results are observed.

## 2. Point-in-time sample timeline

For decision candle `t`:

1. The decision candle is a final 15m trade candle.
2. `decision_time = close_time(t) + 1 ms`.
3. The ATR input contains exactly the decision candle and the preceding 14 closed 15m candles plus one earlier close needed for true range.
4. Simulated entry time is `decision_time + 1,000 ms`.
5. Only the next four contiguous closed 15m candles are inspected.
6. `vertical_barrier_time = close_time(t+4) + 1 ms`.
7. No candle, intrabar or funding event after the vertical barrier may affect the result or lineage.

The primary horizon is 4 bars. Horizons 2 and 8 are declared secondary sensitivity analyses only; they must never be merged into the primary metric.

## 3. ATR and barriers

Version 1 uses simple ATR(14), with no future smoothing:

```text
TR_i  = max(high_i - low_i,
            abs(high_i - close_(i-1)),
            abs(low_i  - close_(i-1)))
ATR14 = sum(TR over decision bar and prior 13 bars) / 14

reference = close of the final decision candle
upper     = reference + 1.0 × ATR14
lower     = reference - 1.0 × ATR14
```

ATR(14) and multiplier 1.0 are the locked v1 baseline, not values selected from the short Stage F audit window. After Stage H creates leakage-safe train/validation/test partitions, any alternative may be selected only from this predeclared sensitivity grid:

- ATR window: `14`, `21`, `28`;
- barrier multiplier: `0.75`, `1.00`, `1.25`, `1.50`;
- horizon: primary `4`; secondary-only `2`, `8`.

Any chosen alternative becomes a new immutable config/version. It may use train and validation only; the final holdout cannot select label parameters.

## 4. Class rules

| Outcome | Label |
|---|---|
| Upper barrier is the first unambiguous touch and net return is greater than `0.0001` | `LONG` |
| Lower barrier is the first unambiguous touch and net return is greater than `0.0001` | `SHORT` |
| No barrier before the vertical barrier | `NO_TRADE / VERTICAL_BARRIER` |
| Barrier gross edge is removed by costs | `NO_TRADE / COST_REMOVED_EDGE` |
| Both barriers touch within the same 1m candle | `NO_TRADE / AMBIGUOUS_INTRABAR` |
| Required candle/intrabar has a prohibited quality flag or the 1m window is incomplete | `NO_TRADE / DATA_QUALITY` |

`net_return == minimum_net_return` is not sufficient; the rule is strictly greater.

## 5. Dual-touch policy

The 1m candles underlying the four future 15m candles are inspected in ascending time order:

- upper-only first → candidate `LONG`;
- lower-only first → candidate `SHORT`;
- both inside the same 1m OHLC candle → `NO_TRADE / AMBIGUOUS_INTRABAR`;
- a 15m barrier touch without a complete matching 1m sequence → `NO_TRADE / DATA_QUALITY`.

The engine never assumes an `open → high → low → close` or `open → low → high → close` path inside one OHLC candle.

## 6. Net cost model

All values are ratios of notional and live in the versioned TOML config:

| Component | v1 assumption | Application |
|---|---:|---|
| Taker fee | `0.0005` per side | entry + exit |
| Half spread | `0.5 bps` per side | entry + exit |
| Slippage | `1.0 bps` per side | entry + exit |
| Latency adverse move | `0.5 bps` | entry only |
| Minimum net edge | `1.0 bps` | strict acceptance threshold |

Fixed round-trip execution cost is therefore `0.00135` (13.5 bps).

The fee is a conservative research assumption matching Binance's published regular-user taker example, not a promise about the operator's live account tier. Binance states that fees vary by VIP level and maker/taker status and may change; a different fee requires a new config version. Binance also defines USDⓈ-M commission as notional × fee rate. See [Binance Futures fee structure](https://www.binance.com/en-KZ/support/faq/detail/360033544231).

Funding is event-based rather than a flat estimate:

```text
events included: entry_time < funding_time <= exit_time
long funding cost  =  sum(realized funding rates)
short funding cost = -sum(realized funding rates)
net return         = gross barrier return - fixed execution cost - funding cost
```

Thus positive funding reduces long returns and increases short returns. Binance documents that funding applies only when a position is held at settlement, and that positive rates flow from longs to shorts; settlement frequency can vary by pair. See [Binance Futures fee types and funding settlement](https://www.binance.com/en-PH/support/faq/detail/98488a516eb84e3eb34605683dffd554).

## 7. Data-quality gate

The following flags prohibit a directional label: `CLOCK_SKEW`, `INCOMPLETE_BAR`, `INVALID_OHLC`, `INVALID_VOLUME`, `MISSING_BAR_BEFORE`, `NEGATIVE_VOLUME`, `NULL_REQUIRED_FIELD`, `OUT_OF_ORDER`, `SOURCE_CONFLICT`, `UNKNOWN_SCHEMA`.

An identical duplicate observation already reconciled by Stage F is not independently disqualifying. The label lineage records all used 15m/1m candle identities and any realized funding identity.

## 8. Volatility regimes for audit

Regimes describe ATR/reference at decision time and are used only to report distribution:

- `LOW`: ratio < `0.003`;
- `NORMAL`: `0.003 ≤ ratio < 0.008`;
- `HIGH`: ratio ≥ `0.008`.

These regimes do not change the label.

## 9. Versioning and reproducibility

The executable config is [`configs/labels/triple-barrier-v1.toml`](../configs/labels/triple-barrier-v1.toml). A label run ID hashes:

- the exact Stage F clean manifest;
- the canonical parsed config hash;
- the label-engine version.

Published label artifacts are immutable and idempotently reused. Any semantic change to ATR, barrier order, class policy, cost, funding, quality gate or timeline requires a new config and/or engine version plus a migration note. Values are stored as decimal strings to avoid binary-float drift.

Binance documents that klines are identified by open time and exposes the 1m/15m intervals used here; see the [official USDⓈ-M kline API](https://developers.binance.com/en/docs/products/derivatives-trading-usds-futures/market-data/rest-api/Kline-Candlestick-Data). External documentation can change, but historical label runs remain bound to their stored inputs and config.

## 10. Acceptance tests

`tests/labels/` contains hand-calculated cases for ATR, long/short barriers, cost removal, funding payment/receipt, dual-touch ambiguity, vertical expiry, data-quality failure, missing intrabars, invalid configs, post-vertical isolation and idempotent publication.
