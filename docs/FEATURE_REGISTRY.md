# Numeric feature registry v1

> Status: `LOCKED FOR STAGE I BASELINE`
>
> Version: `1.0.0`
>
> Decision timestamp rule: only a candle satisfying `close_time < decision_time` is visible.

Stage I uses 13 deterministic numeric features. Every feature is computed independently for each
sample from the immutable Stage F clean run. Missing required history rejects the sample; values are
never forward-filled from the future. `StandardScaler` is fitted on TRAIN only and applied unchanged
to VALIDATION. FINAL_HOLDOUT is sealed.

| Feature | Formula / window | Source | Missing rule |
|---|---|---|---|
| `return_15m_1` | `close[t] / close[t-1] - 1` | closed trade 15m | reject if unavailable |
| `return_15m_4` | `close[t] / close[t-4] - 1` | closed trade 15m | reject if unavailable |
| `trend_1h_1` | `close1h[t] / close1h[t-1] - 1` | closed trade 1H | reject if fewer than 3 bars |
| `trend_1h_3bar` | `(close1h[t] / close1h[t-2] - 1) / 2` | closed trade 1H | reject if fewer than 3 bars |
| `atr_ratio_14` | mean of 14 true ranges / latest close | closed trade 15m | reject if fewer than 15 bars |
| `realized_volatility_4` | population SD of latest three close returns | closed trade 15m | reject if unavailable |
| `range_ratio_15m` | `(high-low)/close` of latest closed bar | closed trade 15m | reject if unavailable |
| `body_ratio_15m` | `(close-open)/close` of latest closed bar | closed trade 15m | reject if unavailable |
| `volume_ratio_4` | latest volume / mean prior three volumes `- 1` | closed trade 15m | zero if denominator is zero |
| `taker_buy_ratio` | taker-buy base volume / base volume | closed trade 15m | zero if volume is zero |
| `mark_trade_basis` | latest mark close / trade close `- 1` | closed mark/trade 15m | reject if unavailable |
| `index_trade_basis` | latest index close / trade close `- 1` | closed index/trade 15m | reject if unavailable |
| `symbol_is_eth` | ETHUSDT `1`, BTCUSDT `0` | declared symbol | reject unknown universe upstream |

True range is `max(high-low, abs(high-prev_close), abs(low-prev_close))`. All output values must be
finite. Stage I intentionally excludes label outcome, barrier time, future return and any data at or
after the decision time. More indicators are not added without an ablation in a new feature version.

Rule baseline v1 uses the sign of `trend_1h_3bar`, the sign/magnitude of `return_15m_4` and the locked
ATR admissibility/filter thresholds in `configs/baselines/baseline-v1.toml`.
