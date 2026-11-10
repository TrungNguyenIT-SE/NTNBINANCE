"""Append-only, content-addressed raw market-data storage."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final
from uuid import uuid4

from ntnbinance.data_contract import SCHEMA_VERSION, require_utc

SENSITIVE_KEYS: Final = frozenset(
    {"apikey", "api_key", "x-mbx-apikey", "secret", "signature", "listenkey", "listen_key"}
)


class RawStoreError(RuntimeError):
    """Raw persistence failed or received unsafe metadata."""


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sanitize_params(params: Mapping[str, object]) -> dict[str, object]:
    """Reject credentials and return stable public request parameters."""

    lowered = {key.lower() for key in params}
    forbidden = lowered & SENSITIVE_KEYS
    if forbidden:
        raise RawStoreError(f"credential-like parameter is forbidden: {sorted(forbidden)}")
    return dict(sorted(params.items()))


@dataclass(frozen=True, slots=True)
class RawRecord:
    """One immutable source observation with point-in-time provenance."""

    dataset: str
    source: str
    endpoint: str
    request_params: dict[str, object]
    record_key: str
    event_time_ms: int
    ingested_at: str
    payload: object
    content_sha256: str
    identity_sha256: str
    schema_version: str = SCHEMA_VERSION

    @classmethod
    def create(
        cls,
        *,
        dataset: str,
        source: str,
        endpoint: str,
        request_params: Mapping[str, object],
        record_key: str,
        event_time_ms: int,
        ingested_at: datetime,
        payload: object,
    ) -> RawRecord:
        if not dataset or not record_key:
            raise RawStoreError("dataset and record_key must be non-empty")
        if source not in {"REST", "WEBSOCKET"}:
            raise RawStoreError(f"unsupported raw source: {source}")
        if not endpoint.startswith(("/fapi/", "/futures/", "wss://fstream.binance.com/")):
            raise RawStoreError("only approved Binance Futures public endpoints are allowed")
        safe_params = sanitize_params(request_params)
        timestamp = require_utc(ingested_at, "ingested_at")
        payload_json = _canonical_json(payload)
        content_hash = _sha256_text(payload_json)
        identity = _sha256_text(f"{dataset}\0{record_key}\0{content_hash}")
        return cls(
            dataset=dataset,
            source=source,
            endpoint=endpoint,
            request_params=safe_params,
            record_key=record_key,
            event_time_ms=event_time_ms,
            ingested_at=timestamp.isoformat().replace("+00:00", "Z"),
            payload=payload,
            content_sha256=content_hash,
            identity_sha256=identity,
        )


@dataclass(frozen=True, slots=True)
class WriteResult:
    """Outcome of one idempotent append operation."""

    batch_id: str
    dataset: str
    written_count: int
    duplicate_count: int
    relative_path: str | None
    file_sha256: str | None


@dataclass(frozen=True, slots=True)
class AuditResult:
    """Verified raw-store totals from manifest, files and identity index."""

    files: int
    records: int
    identities: int
    datasets: dict[str, int]


class RawStore:
    """Persist immutable gzip JSONL batches and an append-only manifest."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.manifest_path = self.root / "manifest.jsonl"
        self.identity_path = self.root / "identity-index.txt"
        self.lock_path = self.root / ".writer.lock"

    def _known_identities(self) -> set[str]:
        if not self.identity_path.exists():
            return set()
        return {
            line.strip()
            for line in self.identity_path.read_text(encoding="ascii").splitlines()
            if line.strip()
        }

    def _acquire_lock(self) -> int:
        self.root.mkdir(parents=True, exist_ok=True)
        try:
            return os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as error:
            raise RawStoreError("another raw-store writer is active") from error

    def audit(self) -> AuditResult:
        """Verify every published raw batch against its append-only manifest."""

        if not self.manifest_path.is_file() or not self.identity_path.is_file():
            raise RawStoreError("raw manifest or identity index is missing")
        identities: set[str] = set()
        datasets: dict[str, int] = {}
        files = 0
        records = 0
        for line in self.manifest_path.read_text(encoding="utf-8").splitlines():
            manifest = json.loads(line)
            if not isinstance(manifest, dict) or not isinstance(manifest.get("path"), str):
                raise RawStoreError("raw manifest entry is invalid")
            destination = (self.root / manifest["path"]).resolve()
            try:
                destination.relative_to(self.root)
            except ValueError as error:
                raise RawStoreError("manifest path escapes raw root") from error
            if not destination.is_file():
                raise RawStoreError(f"manifest file is missing: {manifest['path']}")
            actual_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
            if actual_hash != manifest.get("file_sha256"):
                raise RawStoreError(f"raw file hash mismatch: {manifest['path']}")
            file_records = 0
            with gzip.open(destination, "rt", encoding="utf-8") as source:
                for record_line in source:
                    record = json.loads(record_line)
                    identity = record.get("identity_sha256")
                    dataset = record.get("dataset")
                    if not isinstance(identity, str) or not isinstance(dataset, str):
                        raise RawStoreError("raw record identity/dataset is invalid")
                    if identity in identities:
                        raise RawStoreError(f"duplicate raw identity: {identity}")
                    identities.add(identity)
                    datasets[dataset] = datasets.get(dataset, 0) + 1
                    file_records += 1
            if file_records != manifest.get("record_count"):
                raise RawStoreError(f"raw record count mismatch: {manifest['path']}")
            files += 1
            records += file_records
        indexed = self._known_identities()
        if indexed != identities:
            raise RawStoreError("identity index does not match published raw records")
        return AuditResult(
            files=files,
            records=records,
            identities=len(identities),
            datasets=dict(sorted(datasets.items())),
        )

    def write_batch(
        self,
        records: Iterable[RawRecord],
        *,
        batch_id: str | None = None,
        created_at: datetime | None = None,
    ) -> WriteResult:
        candidates = list(records)
        if not candidates:
            raise RawStoreError("cannot write an empty raw batch")
        datasets = {record.dataset for record in candidates}
        if len(datasets) != 1:
            raise RawStoreError("a raw batch must contain exactly one dataset")
        dataset = next(iter(datasets))
        active_batch_id = batch_id or str(uuid4())
        timestamp = require_utc(created_at or datetime.now(UTC), "created_at")

        lock_fd = self._acquire_lock()
        try:
            known = self._known_identities()
            fresh: list[RawRecord] = []
            seen_in_batch: set[str] = set()
            for record in candidates:
                if record.identity_sha256 in known or record.identity_sha256 in seen_in_batch:
                    continue
                fresh.append(record)
                seen_in_batch.add(record.identity_sha256)

            duplicate_count = len(candidates) - len(fresh)
            if not fresh:
                return WriteResult(
                    batch_id=active_batch_id,
                    dataset=dataset,
                    written_count=0,
                    duplicate_count=duplicate_count,
                    relative_path=None,
                    file_sha256=None,
                )

            relative = (
                Path(dataset)
                / f"ingest_date={timestamp:%Y-%m-%d}"
                / (f"batch_id={active_batch_id}")
                / "part-00000.jsonl.gz"
            )
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=False)
            temporary = destination.with_suffix(destination.suffix + ".tmp")
            with gzip.open(temporary, "wt", encoding="utf-8", newline="\n") as output:
                for record in fresh:
                    output.write(_canonical_json(asdict(record)))
                    output.write("\n")
            os.replace(temporary, destination)
            file_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
            manifest = {
                "batch_id": active_batch_id,
                "created_at": timestamp.isoformat().replace("+00:00", "Z"),
                "dataset": dataset,
                "duplicate_count": duplicate_count,
                "file_sha256": file_hash,
                "max_event_time_ms": max(record.event_time_ms for record in fresh),
                "min_event_time_ms": min(record.event_time_ms for record in fresh),
                "path": relative.as_posix(),
                "record_count": len(fresh),
                "schema_version": SCHEMA_VERSION,
            }
            with self.manifest_path.open("a", encoding="utf-8", newline="\n") as output:
                output.write(_canonical_json(manifest) + "\n")
            with self.identity_path.open("a", encoding="ascii", newline="\n") as output:
                output.writelines(f"{record.identity_sha256}\n" for record in fresh)
            return WriteResult(
                batch_id=active_batch_id,
                dataset=dataset,
                written_count=len(fresh),
                duplicate_count=duplicate_count,
                relative_path=relative.as_posix(),
                file_sha256=file_hash,
            )
        finally:
            os.close(lock_fd)
            self.lock_path.unlink(missing_ok=True)
