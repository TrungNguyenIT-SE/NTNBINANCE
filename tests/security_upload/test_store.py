from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from pathlib import Path

import pytest

from ntnbinance.uploads.api import LocalRateLimiter, read_limited_body
from ntnbinance.uploads.store import SecureImageStore, UploadError

from .helpers import OWNER, VALID_PNG


class FakeRequest:
    def __init__(self, headers: dict[str, str], chunks: list[bytes]) -> None:
        self.headers = headers
        self.chunks = chunks
        self.stream_started = False

    async def stream(self) -> AsyncIterator[bytes]:
        self.stream_started = True
        for chunk in self.chunks:
            yield chunk


def store(
    tmp_path: Path,
    *,
    clock: Callable[[], float] | None = None,
    ttl_seconds: int = 60,
) -> SecureImageStore:
    return SecureImageStore(
        tmp_path / "storage",
        max_upload_bytes=20_000,
        max_image_pixels=1_000_000,
        ttl_seconds=ttl_seconds,
        web_root=tmp_path / "web",
        clock=clock or (lambda: 100.0),
    )


def test_content_length_rejects_before_stream_and_chunk_limit_stops_early() -> None:
    declared = FakeRequest({"content-length": "101"}, [b"should-not-be-read"])
    with pytest.raises(UploadError, match="byte limit") as declared_error:
        asyncio.run(read_limited_body(declared, 100))
    assert declared_error.value.status_code == 413
    assert declared.stream_started is False

    chunked = FakeRequest({}, [b"a" * 60, b"b" * 60, b"unreached"])
    with pytest.raises(UploadError, match="byte limit"):
        asyncio.run(read_limited_body(chunked, 100))
    assert chunked.stream_started is True


@pytest.mark.parametrize("length", ["invalid", "-1"])
def test_invalid_content_length_is_rejected(length: str) -> None:
    request = FakeRequest({"content-length": length}, [])
    with pytest.raises(UploadError) as error:
        asyncio.run(read_limited_body(request, 100))
    assert error.value.code == "CONTENT_LENGTH_INVALID"


def test_cleanup_removes_expired_blob_and_metadata(tmp_path: Path) -> None:
    now = [100.0]
    storage = store(tmp_path, clock=lambda: now[0], ttl_seconds=10)
    record = storage.store(VALID_PNG, content_type="image/png", owner_session_id=OWNER)
    now[0] = 111.0
    assert storage.cleanup_expired() == 1
    assert not list((tmp_path / "storage").rglob(f"*{record.upload_id}*"))
    with pytest.raises(UploadError) as error:
        storage.read(record.upload_id, owner_session_id=OWNER)
    assert error.value.status_code == 404


def test_tampered_blob_and_metadata_fail_integrity_checks(tmp_path: Path) -> None:
    storage = store(tmp_path)
    record = storage.store(VALID_PNG, content_type="image/png", owner_session_id=OWNER)
    blob = tmp_path / "storage/blobs" / record.stored_name
    blob.write_bytes(b"tampered")
    with pytest.raises(UploadError) as blob_error:
        storage.read(record.upload_id, owner_session_id=OWNER)
    assert blob_error.value.code == "STORAGE_CORRUPT"

    metadata = tmp_path / "storage/metadata" / f"{record.upload_id}.json"
    metadata.write_text("not-json", encoding="utf-8")
    with pytest.raises(UploadError) as metadata_error:
        storage.read(record.upload_id, owner_session_id=OWNER)
    assert metadata_error.value.code == "STORAGE_CORRUPT"


def test_metadata_path_injection_is_blocked(tmp_path: Path) -> None:
    storage = store(tmp_path)
    record = storage.store(VALID_PNG, content_type="image/png", owner_session_id=OWNER)
    metadata = tmp_path / "storage/metadata" / f"{record.upload_id}.json"
    raw = json.loads(metadata.read_text(encoding="utf-8"))
    raw["stored_name"] = "../../outside.png"
    metadata.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(UploadError) as error:
        storage.read(record.upload_id, owner_session_id=OWNER)
    assert error.value.code == "STORAGE_PATH_INVALID"


def test_storage_root_must_not_overlap_web_root(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="outside"):
        SecureImageStore(
            tmp_path / "web/uploads",
            max_upload_bytes=100,
            max_image_pixels=100,
            ttl_seconds=1,
            web_root=tmp_path / "web",
        )


def test_rate_limiter_window_expires() -> None:
    now = [10.0]
    limiter = LocalRateLimiter(1, 5, clock=lambda: now[0])
    assert limiter.consume(OWNER) is None
    assert limiter.consume(OWNER) == 5
    now[0] = 15.0
    assert limiter.consume(OWNER) is None
