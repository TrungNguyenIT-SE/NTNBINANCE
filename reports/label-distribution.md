# Stage G label distribution and acceptance report

> Run date: `13/11/2026` (Asia/Saigon)
>
> Result: **PASS — label v1 mechanics and reproducibility**
>
> Label run: `8780c5a42857c830`
>
> Config/engine version: `1.0.0 / 1.0.1`

## Artifact identity

| Artifact | Identity |
|---|---|
| Stage F clean manifest SHA-256 | `ca988a80e7f4704272e317f35bd6dee1d01695a541d3cebea9a6719684c3b13b` |
| Canonical config hash | `35b4571aaa7280290d1e996f7e4aebe9e290db3ab82f6f2c9145cf772f4d6f16` |
| Config file SHA-256 | `DFA36E3E090BD912D092B2F81A4C1459F71E8BDED1BFCD566A05CE5BBCEE73DC` |
| Label JSONL SHA-256 | `ca156100916c3d4d32e17711c5f25697317de8aeb900865da8f0d65852666e55` |
| Label manifest SHA-256 | `AD360F7A0CBE983D22BFF5889638648C9435A7037B890BB24A2649CD4F47C0AF` |

The generated dataset contains 154 unique `(symbol, decision_time)` samples and zero excluded candidate windows. A second execution returned the same run ID with `reused=true`.

## Aggregate distribution

| Label | Count | Share |
|---|---:|---:|
| LONG | 49 | 31.82% |
| SHORT | 67 | 43.51% |
| NO_TRADE | 38 | 24.68% |
| **Total** | **154** | **100.00%** |

No class is absent. The observed SHORT skew is descriptive only; the window is too short to infer a durable regime or model edge.

## By symbol

| Symbol | LONG | SHORT | NO_TRADE | Total |
|---|---:|---:|---:|---:|
| BTCUSDT | 28 | 35 | 14 | 77 |
| ETHUSDT | 21 | 32 | 24 | 77 |

## By UTC decision date

| Date | LONG | SHORT | NO_TRADE | Total |
|---|---:|---:|---:|---:|
| 09/11/2026 | 7 | 2 | 9 | 18 |
| 10/11/2026 | 42 | 65 | 29 | 136 |

The first date is a partial capture boundary and must not be compared with the full second date as equal-duration performance.

## By volatility regime

| ATR/reference regime | LONG | SHORT | NO_TRADE | Total |
|---|---:|---:|---:|---:|
| LOW | 28 | 47 | 12 | 87 |
| NORMAL | 20 | 19 | 22 | 61 |
| HIGH | 1 | 1 | 4 | 6 |

The HIGH bucket contains only six samples and cannot support a statistical conclusion.

## Outcome reasons

| Reason | Count |
|---|---:|
| Upper barrier first, net positive | 49 |
| Lower barrier first, net positive | 67 |
| No touch before vertical barrier | 32 |
| Ambiguous inside one 1m candle | 6 |
| Cost removed edge | 0 |
| Data-quality rejection | 0 |

Five labels crossed an actual funding event and therefore have a non-zero signed funding cost. Absence of `COST_REMOVED_EDGE` in this small window does not remove the cost gate; the hand-calculated tests prove that a gross touch below the configured cost threshold becomes `NO_TRADE`.

## Leakage and determinism checks

- Maximum vertical distance is exactly 3,600,000 ms.
- The engine accepts exactly four contiguous future 15m bars.
- 1m candles and funding events after the vertical barrier are ignored and absent from lineage.
- All 154 rows carry one identical config hash.
- All 154 sample keys are unique.
- Decimal arithmetic is used for price, ATR, fee, funding and returns.
- Reprocessing the same clean manifest/config/engine reuses the immutable run.

## Interpretation boundary

This report validates label definition, class coverage and implementation mechanics. It is not a backtest and does not establish profitability. Stage H must create a purged time split before any parameter comparison; Stage J must validate execution realism and net PnL.

All processing is local and uses existing Stage F data. New cash cost remains **0 VNĐ**.

## Repository quality gate

```text
128 tests passed
statement + branch coverage: 90.33%
Ruff lint/format: pass
mypy strict: pass
pip check: pass
frontend lint/format/typecheck/test/build: pass
```

The same software gate and the packaged label CLI passed in a detached clean worktree; see [`stage-g-clean-checkout.md`](stage-g-clean-checkout.md).
