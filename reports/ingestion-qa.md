# Stage E ingestion QA

> Date: `11/11/2026`
> Result: `PASS — equivalent operating cycle`
> Cash cost added: `0 VNĐ`

## Acceptance interpretation

Exit Gate E permits either a continuous 24-hour trial **or an equivalent operating cycle**. This run did not claim a 24-hour continuously connected WebSocket session. The accepted equivalent cycle combines:

1. A live 24-hour historical window from Binance for every Stage E dataset and both MVP symbols.
2. An immediate rerun proving idempotent duplicate handling while accepting only the newly elapsed minute.
3. A live routed WebSocket capture spanning two 1m close boundaries.
4. Deterministic tests simulating disconnect/resubscription, missing closed intervals, REST recovery, 429/418/5xx, timeout, malformed pages and manifest corruption.
5. A full-file manifest/hash/identity audit.

## Live REST results

Initial 24-hour pull:

| Dataset | BTCUSDT | ETHUSDT | Total written |
|---|---:|---:|---:|
| Trade 1m | 1,440 | 1,440 | 2,880 |
| Mark price 1m | 1,440 | 1,440 | 2,880 |
| Index price 1m | 1,440 | 1,440 | 2,880 |
| OI 5m | 288 | 288 | 576 |
| Funding | 3 | 3 | 6 |
| **Total** | | | **9,222** |

Immediate rerun:

- Funding and OI: all 582 received records detected as duplicates; `0` newly written.
- Each candle series: 1,439 duplicate records and exactly one newly elapsed 1m record.
- No duplicate raw identity was published.

## Live WebSocket results

- URL family: `wss://fstream.binance.com/market/stream`.
- Combined subscriptions: BTCUSDT and ETHUSDT `@kline_1m`.
- Duration: 2 minutes.
- Final closed events persisted: 4 (two symbols across two close boundaries).
- Connection errors: 0.
- API key / listen key used: no.

## Automated resilience evidence

Full repository gate: `91 passed`, statement/branch coverage `94.39%`, Ruff/format/mypy/pip-check/frontend checks all passed.

Stage E focused suite covers:

- finite timeout, exponential backoff and jitter;
- `Retry-After` plus `X-MBX-USED-WEIGHT-*` parsing;
- 408/418/429/5xx and network timeout behavior;
- dynamic request-weight limit and proactive throttle;
- pagination order/progress guards;
- exact raw envelope, gzip batch, manifest and content identity;
- idempotent rerun and changed-payload preservation;
- stream finality, duplicate event and gap detection;
- REST recovery callback before watermark advance;
- reconnect with URL-based resubscription;
- secret-like parameter rejection;
- tampered raw file detection.

## Manifest audit

```text
files:      26
records:    9,232
identities: 9,232
result:     PASS
```

Integrity hashes and dataset counts are recorded in `reports/stage-e-manifest-snapshot.md`.

## Clean-checkout reproducibility

Commit `cff6811b4e4b93028822456b946b9d0c6f385243` was cloned into a new local directory and verified from no pre-existing virtual environment or `node_modules`:

```text
setup from requirements.lock/package-lock.json: PASS
websockets==17.4 installed: PASS
pip dependency consistency: PASS
pytest: 91 passed
coverage: 94.39%
frontend check/build: PASS
backend smoke: PASS
frontend smoke: PASS
Git checkout status: clean
```

## Limitations and next gate

- This is not evidence of 24-hour continuous WebSocket uptime; a longer soak remains recommended before paper trading.
- Stage E proves ingestion and recovery mechanics, not clean-data quality.
- Duplicate/missing/out-of-order analysis, quarantine, resampling and ≥99.9% coverage belong to Stage F.

## Conclusion

The pipeline can be rerun without publishing identical duplicates; live public data is captured with provenance; a missing stream interval is detected and recovered through REST in the equivalent-cycle test. Exit Gate E passes without paid infrastructure or trading credentials.
