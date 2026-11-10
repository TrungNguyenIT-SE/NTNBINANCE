import gzip
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from ntnbinance.ingestion.raw_store import RawRecord, RawStore, RawStoreError, sanitize_params

NOW = datetime(2026, 11, 11, 12, 0, tzinfo=UTC)


def record(*, payload: object | None = None, dataset: str = "trade_klines") -> RawRecord:
    return RawRecord.create(
        dataset=dataset,
        source="REST",
        endpoint="/fapi/v1/klines",
        request_params={"symbol": "BTCUSDT", "limit": 2},
        record_key="BTCUSDT|1m|1000",
        event_time_ms=1999,
        ingested_at=NOW,
        payload=payload if payload is not None else [1000, "1.0", 1999],
    )


def test_write_batch_creates_gzip_manifest_hash_and_identity_index(tmp_path: Path) -> None:
    store = RawStore(tmp_path / "raw")
    item = record()

    result = store.write_batch([item], batch_id="batch-one", created_at=NOW)

    assert result.written_count == 1
    assert result.duplicate_count == 0
    assert result.relative_path is not None
    destination = store.root / result.relative_path
    assert destination.is_file()
    with gzip.open(destination, "rt", encoding="utf-8") as source:
        saved = json.loads(source.read())
    assert saved["identity_sha256"] == item.identity_sha256
    manifest = json.loads(store.manifest_path.read_text(encoding="utf-8"))
    assert manifest["file_sha256"] == result.file_sha256
    assert manifest["record_count"] == 1
    assert store.identity_path.read_text(encoding="ascii").strip() == item.identity_sha256
    audit = store.audit()
    assert (audit.files, audit.records, audit.identities) == (1, 1, 1)
    assert audit.datasets == {"trade_klines": 1}


def test_rerun_and_duplicate_inside_batch_are_idempotent(tmp_path: Path) -> None:
    store = RawStore(tmp_path / "raw")
    item = record()

    first = store.write_batch([item, item], batch_id="first", created_at=NOW)
    second = store.write_batch([item], batch_id="second", created_at=NOW)

    assert (first.written_count, first.duplicate_count) == (1, 1)
    assert (second.written_count, second.duplicate_count) == (0, 1)
    assert second.relative_path is None
    assert len(store.manifest_path.read_text(encoding="utf-8").splitlines()) == 1


def test_same_key_with_changed_payload_is_preserved_as_raw_conflict(tmp_path: Path) -> None:
    store = RawStore(tmp_path / "raw")
    first = record(payload=[1000, "1.0", 1999])
    changed = record(payload=[1000, "1.1", 1999])

    store.write_batch([first], batch_id="first", created_at=NOW)
    result = store.write_batch([changed], batch_id="changed", created_at=NOW)

    assert result.written_count == 1
    assert first.identity_sha256 != changed.identity_sha256


@pytest.mark.parametrize(
    "params",
    [{"apiKey": "secret"}, {"signature": "secret"}, {"listenKey": "secret"}],
)
def test_credentials_are_rejected(params: dict[str, object]) -> None:
    with pytest.raises(RawStoreError, match="credential-like"):
        sanitize_params(params)


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"dataset": ""}, "non-empty"),
        ({"source": "PRIVATE"}, "unsupported raw source"),
        ({"endpoint": "https://example.com"}, "approved Binance"),
    ],
)
def test_invalid_record_metadata_is_rejected(overrides: dict[str, object], message: str) -> None:
    values: dict[str, object] = {
        "dataset": "trade_klines",
        "source": "REST",
        "endpoint": "/fapi/v1/klines",
        "request_params": {},
        "record_key": "key",
        "event_time_ms": 1,
        "ingested_at": NOW,
        "payload": {},
    }
    values.update(overrides)
    with pytest.raises(RawStoreError, match=message):
        RawRecord.create(**values)  # type: ignore[arg-type]


def test_empty_mixed_dataset_and_concurrent_writer_are_rejected(tmp_path: Path) -> None:
    store = RawStore(tmp_path / "raw")
    with pytest.raises(RawStoreError, match="empty"):
        store.write_batch([])
    with pytest.raises(RawStoreError, match="exactly one"):
        store.write_batch([record(), record(dataset="mark_price_klines")])
    store.root.mkdir(parents=True)
    store.lock_path.write_text("held", encoding="ascii")
    with pytest.raises(RawStoreError, match="another raw-store writer"):
        store.write_batch([record()])


def test_audit_rejects_missing_and_tampered_store(tmp_path: Path) -> None:
    store = RawStore(tmp_path / "raw")
    with pytest.raises(RawStoreError, match="manifest or identity"):
        store.audit()
    result = store.write_batch([record()], batch_id="batch", created_at=NOW)
    assert result.relative_path is not None
    destination = store.root / result.relative_path
    destination.write_bytes(destination.read_bytes() + b"tampered")
    with pytest.raises(RawStoreError, match="hash mismatch"):
        store.audit()
