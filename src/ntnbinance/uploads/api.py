"""Raw-body image upload API with streaming byte limits and local rate limiting."""

from __future__ import annotations

import re
import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator, Callable
from threading import RLock
from typing import Protocol

from fastapi import APIRouter, FastAPI, Header, HTTPException, Request, Response

from ntnbinance.config import PROJECT_ROOT, Settings
from ntnbinance.uploads.store import SecureImageStore, UploadError

SESSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


class StreamRequest(Protocol):
    @property
    def headers(self) -> object: ...

    def stream(self) -> AsyncIterator[bytes]: ...


class LocalRateLimiter:
    def __init__(
        self,
        limit: int,
        window_seconds: int,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self.clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = RLock()

    def consume(self, key: str) -> int | None:
        now = self.clock()
        threshold = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= threshold:
                events.popleft()
            if len(events) >= self.limit:
                return max(1, int(events[0] + self.window_seconds - now + 0.999))
            events.append(now)
            return None


def _header(headers: object, name: str) -> str | None:
    getter = getattr(headers, "get", None)
    if getter is None:
        return None
    value = getter(name)
    return value if isinstance(value, str) else None


async def read_limited_body(request: StreamRequest, max_bytes: int) -> bytes:
    encoding = (_header(request.headers, "content-encoding") or "identity").lower()
    if encoding != "identity":
        raise UploadError("CONTENT_ENCODING_REJECTED", "Compressed request bodies are not allowed")
    raw_length = _header(request.headers, "content-length")
    if raw_length is not None:
        try:
            declared_length = int(raw_length)
        except ValueError as error:
            raise UploadError(
                "CONTENT_LENGTH_INVALID", "Content-Length must be an integer"
            ) from error
        if declared_length < 0:
            raise UploadError("CONTENT_LENGTH_INVALID", "Content-Length cannot be negative")
        if declared_length > max_bytes:
            raise UploadError("UPLOAD_TOO_LARGE", "Image exceeds the configured byte limit", 413)

    payload = bytearray()
    async for chunk in request.stream():
        if len(payload) + len(chunk) > max_bytes:
            raise UploadError("UPLOAD_TOO_LARGE", "Image exceeds the configured byte limit", 413)
        payload.extend(chunk)
    if not payload:
        raise UploadError("EMPTY_UPLOAD", "Image body is empty")
    return bytes(payload)


def _session(value: str | None) -> str:
    if value is None or SESSION_PATTERN.fullmatch(value) is None:
        raise HTTPException(status_code=401, detail={"code": "SESSION_INVALID"})
    return value


def _http_error(error: UploadError) -> HTTPException:
    return HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": str(error)},
    )


def register_upload_api(app: FastAPI, settings: Settings) -> None:
    store = SecureImageStore(
        settings.runtime_root / "uploads",
        max_upload_bytes=settings.max_upload_bytes,
        max_image_pixels=settings.max_image_pixels,
        ttl_seconds=settings.upload_ttl_seconds,
        web_root=PROJECT_ROOT / "apps" / "web",
    )
    limiter = LocalRateLimiter(settings.upload_rate_limit, settings.upload_rate_window_seconds)
    app.state.upload_store = store
    app.state.upload_limiter = limiter
    router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])

    @router.post("/images", status_code=201)
    async def upload_image(
        request: Request,
        x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    ) -> dict[str, str | int | float | bool]:
        owner = _session(x_session_id)
        retry_after = limiter.consume(owner)
        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail={"code": "RATE_LIMITED"},
                headers={"Retry-After": str(retry_after)},
            )
        try:
            payload = await read_limited_body(request, settings.max_upload_bytes)
            store.cleanup_expired()
            record = store.store(
                payload,
                content_type=request.headers.get("content-type", ""),
                owner_session_id=owner,
            )
        except UploadError as error:
            raise _http_error(error) from error
        return record.public()

    @router.get("/images/{upload_id}")
    def read_image(
        upload_id: str,
        x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    ) -> Response:
        owner = _session(x_session_id)
        try:
            record, payload = store.read(upload_id, owner_session_id=owner)
        except UploadError as error:
            raise _http_error(error) from error
        return Response(
            payload,
            media_type="image/png",
            headers={
                "Cache-Control": "no-store",
                "Content-Disposition": f'inline; filename="{record.upload_id}.png"',
                "X-Content-Type-Options": "nosniff",
            },
        )

    @router.delete("/images/{upload_id}", status_code=204)
    def delete_image(
        upload_id: str,
        x_session_id: str | None = Header(default=None, alias="X-Session-ID"),
    ) -> Response:
        owner = _session(x_session_id)
        try:
            store.delete(upload_id, owner_session_id=owner)
        except UploadError as error:
            raise _http_error(error) from error
        return Response(status_code=204)

    app.include_router(router)
