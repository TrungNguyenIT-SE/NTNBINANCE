# Data Contract and Time Semantics

> Version: `1.0.0` — locked 09/11/2026
> Applies to: ingest, clean, feature, training, backtest and inference

## 1. Non-negotiable rules

1. Storage and computation use UTC. UI may display `Asia/Ho_Chi_Minh` but exchanges explicit-offset ISO 8601 values.
2. Naive timestamps and non-zero storage offsets are rejected, not guessed.
3. Prediction inputs contain only records knowable at `decision_time`.
4. A candle is eligible only if `is_closed=true` and `available_at <= decision_time`.
5. Raw data is append-only; corrections add lineage instead of hiding history.
6. Clean keys are deterministic; equal duplicates are idempotent and conflicting finals are quarantined.
7. Unknown schema versions fail closed.

The executable source is `src/ntnbinance/data_contract.py`; prose and code change together.

## 2. Timestamp semantics

| Timestamp | Definition | Use |
|---|---|---|
| `open_time` | Inclusive UTC candle start. | Identity and alignment. |
| `close_time` | Inclusive last millisecond: `open_time + interval - 1 ms`. | Boundary validation, not proof of local availability. |
| `event_time` | Source event time; REST candle fallback is `close_time`. | Source ordering and availability. |
| `ingested_at` | Local UTC instant after full payload receipt. | Availability, latency and lineage. |
| `decision_time` | Immutable UTC prediction/backtest decision instant. | Upper bound for all inputs. |
| `funding_time` | Effective realized funding time. | Funding identity/availability. |

For candles: `available_at = max(close_time + 1 ms, event_time, ingested_at)`. The added millisecond converts Binance's inclusive close to the next half-open boundary.

```text
open_time      12:00:00.000Z
close_time     12:14:59.999Z
ingested_at    12:15:00.220Z
available_at   12:15:00.220Z
```

A decision at `12:15:00.100Z` rejects this candle. A later decision may use it only when `is_closed=true`.

## 3. Closed-candle/no-look-ahead gate

Every prediction, labeler, feature query and backtest enforces:

```text
schema_version == supported_version
is_closed == true
close_time + 1 ms <= decision_time
event_time <= decision_time
ingested_at <= decision_time
no critical quality flag
```

WebSocket finality comes from its closed-kline indicator. A REST row is closed only after the reconciliation clock passes its exclusive boundary. The in-progress last REST bar is discarded or remains staging with `is_closed=false`.

Historical training uses a simulated historical `decision_time`; a later backfill time is not evidence of historical availability. Reconstruction uses earliest valid provenance or a documented conservative rule.

## 4. Idempotency and conflicts

- Same key and same normalized content: idempotent duplicate; retain lineage, one clean row.
- Same key while open: retain raw updates; publish only the final closed version.
- Same key with conflicting final content: flag `SOURCE_CONFLICT`, quarantine and reconcile through REST.
- Trade/mark/index at the same open time do not collide because `price_kind` is in the key.
- Schema changes require a semantic version, migration note, compatibility test and regenerated clean partitions.

## 5. Raw, clean and feature layers

Storage is local Parquet queried by DuckDB; neither requires a paid service.

```text
data/raw/{dataset}/ingest_date=YYYY-MM-DD/batch_id={uuid}/part-*.jsonl.gz
data/clean/{dataset}/schema_version=1.0.0/symbol={symbol}/date=YYYY-MM-DD/part-*.parquet
data/features/{feature_set}/version={version}/symbol={symbol}/decision_date=YYYY-MM-DD/part-*.parquet
var/{profile}/catalog.duckdb
```

### Raw

- Append-only exact payload plus request/stream envelope, receive time, endpoint, status, batch ID and SHA-256.
- Never directly trains a model.
- Manifest stores hash, bytes, rows, event-time range and ingest status.

### Clean

- Typed, deduplicated, UTC Parquet with schema, key, flags and `raw_ref`.
- Atomic publication: write candidate, validate, rename, then add to manifest.
- DuckDB views read only published manifest entries.

### Feature

- Point-in-time correct and derived only from clean rows passing the availability gate.
- Key starts `(feature_set_version, symbol, decision_time)`.
- Stores source watermark, maximum input `available_at`, code revision and manifest hash.
- Formula changes create a new version; features remain rebuildable.

Parquet uses `zstd`. Initial row-group target is 64–128 MiB; files under 16 MiB are compacted deterministically after Stage E/F measurement validates memory behavior.

## 6. Retention and disk policy

| Class | Default retention | Rule |
|---|---|---|
| Raw market payloads/manifests | Indefinite for MVP | Monthly compaction; never delete while a release references them. |
| Clean market data | Current + previous schema | Rebuildable; remove older unreferenced versions only after validation. |
| Features | Latest 3 versions or 180 days | Pin anything referenced by a model/report. |
| Uploaded chart images | 30 days | Local only; immediate user deletion supported; no training without opt-in. |
| Crops/embeddings | Same as source | Cascade-delete by upload ID unless a consented run pins them. |
| Application logs | 30 days | Daily rotation; redact secrets, payload images and sensitive paths. |
| Evaluation/audit logs | 180 days | Keep IDs/hashes/outcomes, not original images. |
| Failed/temp jobs | 7 days | Delete only objects absent from published manifests. |
| Candidate models | Best 3 per experiment, 90 days | Pin baseline/promoted artifacts. |
| Promoted model/repro bundle | Indefinite | Retain until retired and unreferenced. |

At 80% disk utilization, pause new backfills and report large managed partitions. Never silently delete raw data, models or uploads. Backup remains the local operator's responsibility in zero-cost scope.

## 7. Validation order and failure behavior

1. Attach immutable raw lineage.
2. Validate schema and required fields.
3. Validate aware UTC timestamps and interval boundary.
4. Validate identity, uniqueness and ordering.
5. Validate finality and point-in-time availability.
6. Validate numeric invariants in Stage F.
7. Attach flags and quarantine critical rows.
8. Verify candidate Parquet counts/hash/schema, then publish atomically.

If required 15m/1h inputs are absent, open, late, conflicting or unknown-schema, inference fails closed to `NO_TRADE`; it never falls back to an open candle.

## 8. Contract changes

- Patch: clarification/backward-compatible optional field.
- Minor: backward-compatible dataset or field addition.
- Major: key, type, meaning, timestamp or nullability break.

Every change updates both documents, executable predicates, tests, migration note and compatibility review. Version `1.0.0` is locked before Stage E begins.

## 9. Acceptance evidence

- `tests/data_contract/test_time_contract.py`: UTC, interval boundary, closure, late/future input and schema.
- `tests/data_contract/test_identity_contract.py`: keys, price-kind isolation, duplicate rejection and quality flags.
- `.venv/Scripts/python.exe -m pytest tests/data_contract --no-cov` must pass before large ingest; the full quality gate enforces package coverage.
- Full repository quality gate must remain green.
