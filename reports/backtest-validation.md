# Stage J execution-aware backtest validation

> Validation date: `15/11/2026` (Asia/Saigon)
>
> Result: **PASS mechanics — NO-GO on trading edge**

## Locked identity and leakage boundary

- Run ID: `efac5d1adcec0a1c`
- Artifact SHA-256: `a322b0d8e58db2a1f55eee963f00da2894402c4931e78ab79e1e753fb23956ec`
- Config hash: `b26f9e30f56d5aad7760199cd937542b8a5231804e7eff1aab2541b14e037d5c`
- Baseline artifact SHA-256: `8c56c1b6a80fb1a5edf22185a337fbfe9967cc00d2b0fdc08035951771e4cbcf`
- Exchange snapshot SHA-256: `d374430b09476521c29bc2f2f5e151019f35bbe8ceef0983dafa4063eca34643`
- Evaluation partition: VALIDATION only (`26` samples).
- FINAL_HOLDOUT opened: `false`; target labels read: `0`.

## Base scenario

| Scenario | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| base | 20 | -0.4080 | -2.5634 | -0.1282 | 0.3576 | 2.6607 | -134.4423 | -119.9686 |

Signals: `20`; partial fills: `0`; unfilled: `0`; win rate: `45.00%`.

Cost decomposition: spread/slippage `0.5018` USDT; fees `1.6537` USDT; funding `0.0000` USDT.
Exits: take-profit `9`, stop-loss `9`, vertical `2`.

`*` Sharpe/Sortino are zero-risk-rate, 15m-annualized diagnostics over only 13 validation decision timestamps. They are reported for completeness, not statistical evidence.

## Execution-cost stress

| Multiplier | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cost x1.0 | 20 | -0.4080 | -2.5634 | -0.1282 | 0.3576 | 2.6607 | -134.4423 | -119.9686 |
| cost x1.5 | 20 | -0.5156 | -3.7460 | -0.1873 | 0.2014 | 3.7973 | -177.7257 | -134.5004 |
| cost x2.0 | 20 | -0.6711 | -4.9749 | -0.2487 | 0.1005 | 5.1677 | -211.5096 | -143.4489 |

## Latency stress

| Latency ms | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1000 | 20 | -0.4080 | -2.5634 | -0.1282 | 0.3576 | 2.6607 | -134.4423 | -119.9686 |
| 61000 | 20 | -0.3328 | -2.4880 | -0.1244 | 0.3645 | 2.8794 | -134.0259 | -120.2351 |
| 121000 | 20 | -0.3415 | -2.4971 | -0.1249 | 0.3448 | 2.5295 | -138.9112 | -116.8383 |

## Required segment analysis

### By confidence

| Segment | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.45-<0.60 | 14 | -0.0727 | -1.5845 | -0.1132 | 0.3909 | 1.7775 | -105.3154 | -97.8522 |
| < 0.45 | 2 | 0.0371 | -0.2197 | -0.1098 | 0.5751 | 0.5170 | -24.3657 | -30.0638 |
| >= 0.60 | 4 | -0.3725 | -0.7592 | -0.1898 | 0.1293 | 0.7592 | -175.8569 | -141.0348 |

### By month

| Segment | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026-11 | 20 | -0.4080 | -2.5634 | -0.1282 | 0.3576 | 2.6607 | -134.4423 | -119.9686 |

### By regime

| Segment | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LOW | 13 | 0.2918 | -0.9650 | -0.0742 | 0.4500 | 1.1019 | -65.9691 | -69.9055 |
| NORMAL | 7 | -0.6998 | -1.5985 | -0.2284 | 0.2850 | 1.8958 | -75.5769 | -78.9236 |

### By side

| Segment | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LONG | 12 | -0.8765 | -2.2587 | -0.1882 | 0.2732 | 2.6501 | -111.9747 | -109.3318 |
| NO_TRADE | 0 | 0.0000 | 0.0000 | 0.0000 | N/A | 0.0000 | N/A | N/A |
| SHORT | 8 | 0.4685 | -0.3048 | -0.0381 | 0.6547 | 0.6218 | -33.5745 | -39.5781 |

### By symbol

| Segment | Filled | Gross PnL | Net PnL | Expectancy | PF | Max DD | Sharpe* | Sortino* |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 13 | 0.2918 | -0.9650 | -0.0742 | 0.4500 | 1.1019 | -65.9691 | -69.9055 |
| ETHUSDT | 7 | -0.6998 | -1.5985 | -0.2284 | 0.2850 | 1.8958 | -75.5769 | -78.9236 |

## Event and fill policy

`decision → configured latency → next eligible 1m open → manage → barrier/vertical exit`. Entry never uses the decision close. Buy fills round up and sell fills round down to the price tick after adverse half-spread/slippage. Quantity rounds down to step size and must satisfy quantity/notional filters. IOC participation caps fills; the remainder is cancelled. A candle touching stop and take uses stop first.

Fees apply to entry and exit notionals; realized funding applies only when its event time is after entry and no later than exit. Gross/net PnL, expectancy, PF, drawdown, Sharpe and Sortino are calculated from actual simulated fills.

## Limitations and decision

The 1m OHLCV data cannot reconstruct order-book depth or sub-minute path. Partial fills use a conservative candle-volume participation proxy. Instrument filters are a current exchangeInfo snapshot, because Stage E did not persist a historical metadata version valid at each decision. Liquidation, leverage, ADL and portfolio margin are out of scope; notional is fixed at 100 USDT with ample simulated equity.

The engine passes mechanical/no-lookahead validation, but the base scenario remains net negative. Stage J therefore does **not** establish edge, production readiness or permission for live trading.

## Verification gates

- Backtest suite: `12 passed`.
- Full Python suite: `160 passed`; statement + branch coverage: `90.48%`.
- Ruff, mypy strict, dependency consistency, ESLint, Prettier, TypeScript, Vitest and production build: `PASS`.
- Artifact generation is byte-for-byte deterministic for identical locked inputs.

## Reproduction

```powershell
powershell -File scripts/run-backtest.ps1
```

All processing is local with existing hardware and public cached market data. New cash cost remains **0 VNĐ**.
