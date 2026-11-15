# Numeric feature registry

## Feature set v2 — Stage N locked

> Version: `2.0.0`
>
> Status: `LOCKED`
>
> Config: `configs/features/feature-set-v2.toml`
>
> Decision rule: `event_time_ms < decision_time_ms` and `close_time_ms < decision_time_ms`

Feature set v2 contains 20 deterministic values. Computation uses `Decimal`; conversion to finite
`float64` happens only at the model boundary. Each vector records every `(dataset, event_time_ms)` used
and asserts `max_event_time_ms < decision_time_ms`.

| Feature | Formula | Window/source | Missing-value rule |
|---|---|---|---|
| `return_15m_1` | `close[t]/close[t-1]-1` | 2 closed trade 15m | reject sample |
| `return_15m_4` | `close[t]/close[t-4]-1` | 5 closed trade 15m | reject sample |
| `return_15m_16` | `close[t]/close[t-16]-1` | 17 closed trade 15m | reject sample |
| `realized_volatility_4` | population SD of 4 close returns | 5 closed trade 15m | reject sample |
| `realized_volatility_16` | population SD of 16 close returns | 17 closed trade 15m | reject sample |
| `atr_ratio_14` | mean of 14 true ranges / latest close | 15 closed trade 15m | reject sample |
| `range_ratio_15m` | `(high-low)/close` | latest trade 15m | reject sample |
| `body_ratio_15m` | `(close-open)/close` | latest trade 15m | reject sample |
| `upper_wick_ratio_15m` | `(high-max(open,close))/close` | latest trade 15m | reject sample |
| `lower_wick_ratio_15m` | `(min(open,close)-low)/close` | latest trade 15m | reject sample |
| `trend_1h_1` | `close1h[t]/close1h[t-1]-1` | 2 closed trade 1h | reject sample |
| `trend_1h_3` | `(close1h[t]/close1h[t-3]-1)/3` | 4 closed trade 1h | reject sample |
| `trigger_15m_atr` | `return_15m_4/atr_ratio_14` | 15m trigger + ATR | zero only if observed ATR is zero |
| `volume_ratio_4` | `volume[t]/mean(volume[t-3:t])-1` | 4 closed trade 15m | missing rejects; zero if observed denominator is zero |
| `volume_zscore_20` | `(volume[t]-mean20)/population_sd20` | 20 closed trade 15m | missing rejects; zero if observed SD is zero |
| `taker_buy_ratio` | `taker_buy_base/volume_base` | latest trade 15m | missing rejects; zero if observed volume is zero |
| `trade_count_ratio_4` | `count[t]/mean(count[t-3:t])-1` | 4 closed trade 15m | missing rejects; zero if observed denominator is zero |
| `mark_trade_basis` | `mark_close/trade_close-1` | exact aligned closed 15m | reject if absent/duplicate/unaligned |
| `index_trade_basis` | `index_close/trade_close-1` | exact aligned closed 15m | reject if absent/duplicate/unaligned |
| `symbol_is_eth` | ETHUSDT `1`, BTCUSDT `0` | declared MVP symbol | reject unsupported symbol |

True range is `max(high-low, abs(high-prev_close), abs(low-prev_close))`. Population SD is used so
training and inference have identical deterministic behavior. All OHLC invariants, non-negative volume
and `taker_buy_volume <= volume` are validated before calculation.

### Context coverage decisions

Coverage requires both completeness and a meaningful calendar span; 100% of a tiny capture is not
treated as production history.

| Context | Observed audit | Gate | v2 decision |
|---|---:|---|---|
| Mark/index basis | 380/380 aligned source rows, 2 days | ≥99.9%, ≥1 day | **INCLUDE** |
| Funding | 6/6 events, 1 day | ≥99%, ≥30 days | **EXCLUDE — span too short** |
| Open interest | 576/576 periods, 2 days | ≥99%, ≥30 days | **EXCLUDE — span too short** |

Funding/OI may enter only a new feature version after the same gate passes on a longer immutable clean
run. They must never be silently forward-filled. Basis is required and exact-time aligned in v2.

### Point-in-time and split rules

- Closed records at or after decision time are invisible, including exact equality.
- Future outliers may be appended to any input without changing any of the 20 values.
- Duplicate timestamps fail closed; sorting does not resolve ambiguous duplicates.
- No label, barrier result, future return or final-holdout target is an input.
- Scaling/imputation fit remains TRAIN-only in Stage O. This engine performs no learned transform.

### Stage N ablation

The development-only stability audit used 152 vectors from clean run `13f11d10018f9914`, produced no
missing/non-finite values and did not open FINAL_HOLDOUT. It removed raw price level (non-stationary),
quote-volume ratio (redundant), `taker_imbalance` (exact affine duplicate of `taker_buy_ratio`) and
funding/OI (coverage span gate). The high return/body correlation in this short trending capture is
reported but not used to remove a semantically distinct feature. Predictive ablation belongs to Stage
O and may use TRAIN/VALIDATION only.

Evidence: `reports/feature-ablation.md`, `reports/feature-ablation.json`, `tests/features/`.

## Historical feature set v1 — Stage I baseline

Version `1.0.0` remains immutable for reproducibility of `reports/baseline-v1.md`. It contains the 13
features used by the Stage I baseline implementation in `ntnbinance.baselines.data`. Stage N does not
rewrite or relabel that historical experiment; Stage O must explicitly select v2.
