"""Validated image decoding, metadata stripping and owner-scoped local storage."""

from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import time
import warnings
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from threading import RLock
from uuid import UUID, uuid4

from PIL import Image, ImageFile, ImageOps, UnidentifiedImageError

ALLOWED_MIME_TO_FORMAT = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}
MIN_WIDTH = 800
MIN_HEIGHT = 600
MAX_EDGE = 4096


class UploadError(ValueError):
    """A safe, structured upload error suitable for an API response."""

    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class StoredImage:
    upload_id: str
    owner_session_hash: str
    source_format: str
    source_sha256: str
    stored_sha256: str
    stored_name: str
    width: int
    height: int
    encoded_bytes: int
    created_at_epoch: float
    expires_at_epoch: float
    deduplicated: bool = False

    def public(self) -> dict[str, str | int | float | bool]:
        return {
            "upload_id": self.upload_id,
            "source_format": self.source_format,
            "sha256": self.stored_sha256,
            "width": self.width,
            "height": self.height,
            "encoded_bytes": self.encoded_bytes,
            "created_at_epoch": self.created_at_epoch,
            "expires_at_epoch": self.expires_at_epoch,
            "deduplicated": self.deduplicated,
        }


def _sniff_format(payload: bytes) -> str | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return "PNG"
    if payload.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if len(payload) >= 12 and payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        return "WEBP"
    return None


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _owner_hash(owner_session_id: str) -> str:
    return hashlib.sha256(owner_session_id.encode("utf-8")).hexdigest()


class SecureImageStore:
    """Store re-encoded PNGs under UUID names with sidecar owner metadata."""

    def __init__(
        self,
        root: Path,
        *,
        max_upload_bytes: int,
        max_image_pixels: int,
        ttl_seconds: int,
        web_root: Path,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.root = root.resolve()
        self.web_root = web_root.resolve()
        if _is_within(self.root, self.web_root) or _is_within(self.web_root, self.root):
            raise ValueError("upload storage must be outside the web root")
        self.blob_root = self.root / "blobs"
        self.metadata_root = self.root / "metadata"
        self.max_upload_bytes = max_upload_bytes
        self.max_image_pixels = max_image_pixels
        self.ttl_seconds = ttl_seconds
        self.clock = clock
        self._lock = RLock()

    def _ensure_roots(self) -> None:
        self.blob_root.mkdir(parents=True, exist_ok=True)
        self.metadata_root.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, root: Path, name: str) -> Path:
        candidate = (root / name).resolve()
        if not _is_within(candidate, root.resolve()):
            raise UploadError("STORAGE_PATH_INVALID", "Stored path escaped its storage root", 500)
        return candidate

    @staticmethod
    def _canonical_id(upload_id: str) -> str:
        try:
            parsed = UUID(upload_id)
        except ValueError as error:
            raise UploadError("UPLOAD_NOT_FOUND", "Upload does not exist", 404) from error
        if str(parsed) != upload_id:
            raise UploadError("UPLOAD_NOT_FOUND", "Upload does not exist", 404)
        return upload_id

    def _metadata_path(self, upload_id: str) -> Path:
        canonical = self._canonical_id(upload_id)
        return self._safe_path(self.metadata_root, f"{canonical}.json")

    def _decode_and_sanitize(
        self, payload: bytes, content_type: str
    ) -> tuple[bytes, str, int, int]:
        declared = content_type.partition(";")[0].strip().lower()
        expected_format = ALLOWED_MIME_TO_FORMAT.get(declared)
        if expected_format is None:
            raise UploadError(
                "MIME_NOT_ALLOWED", "Content-Type must be image/png, image/jpeg or image/webp"
            )
        magic_format = _sniff_format(payload)
        if magic_format is None:
            raise UploadError("MAGIC_INVALID", "File signature is not an allowed image")
        if magic_format != expected_format:
            raise UploadError("MIME_MAGIC_MISMATCH", "Content-Type does not match file signature")

        ImageFile.LOAD_TRUNCATED_IMAGES = False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(payload)) as probe:
                    source_format = probe.format
                    width, height = probe.size
                    frames = getattr(probe, "n_frames", 1)
                    if source_format != magic_format:
                        raise UploadError(
                            "DECODER_FORMAT_MISMATCH", "Decoder format conflicts with signature"
                        )
                    if frames != 1 or getattr(probe, "is_animated", False):
                        raise UploadError(
                            "ANIMATED_IMAGE", "Animated or multi-frame images are not allowed"
                        )
                    self._validate_dimensions(width, height)
                    probe.verify()
                with Image.open(io.BytesIO(payload)) as source:
                    source.load()
                    transposed = ImageOps.exif_transpose(source)
                    self._validate_dimensions(*transposed.size)
                    clean = transposed.convert("RGB")
                    output = io.BytesIO()
                    clean.save(
                        output,
                        format="PNG",
                        optimize=True,
                        exif=b"",
                        icc_profile=None,
                    )
        except UploadError:
            raise
        except (Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
            raise UploadError(
                "PIXEL_LIMIT_EXCEEDED", "Decoded image exceeds pixel safety limit"
            ) from error
        except (OSError, SyntaxError, UnidentifiedImageError) as error:
            raise UploadError(
                "IMAGE_DECODE_FAILED", "Image is corrupt or cannot be decoded"
            ) from error
        return output.getvalue(), magic_format, clean.width, clean.height

    def _validate_dimensions(self, width: int, height: int) -> None:
        if width < MIN_WIDTH or height < MIN_HEIGHT or width > MAX_EDGE or height > MAX_EDGE:
            raise UploadError(
                "DIMENSIONS_INVALID", "Image dimensions are outside the locked envelope"
            )
        if width * height > self.max_image_pixels:
            raise UploadError("PIXEL_LIMIT_EXCEEDED", "Decoded image exceeds pixel safety limit")

    def _load_record(self, path: Path) -> StoredImage:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return StoredImage(**raw)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise UploadError(
                "STORAGE_CORRUPT", "Upload metadata failed integrity validation", 500
            ) from error

    def _owned_record(self, upload_id: str, owner_session_id: str) -> StoredImage:
        path = self._metadata_path(upload_id)
        if not path.is_file():
            raise UploadError("UPLOAD_NOT_FOUND", "Upload does not exist", 404)
        record = self._load_record(path)
        if not hmac.compare_digest(record.owner_session_hash, _owner_hash(owner_session_id)):
            raise UploadError("UPLOAD_NOT_FOUND", "Upload does not exist", 404)
        if record.expires_at_epoch <= self.clock():
            raise UploadError("UPLOAD_NOT_FOUND", "Upload does not exist", 404)
        return record

    def _find_duplicate(self, owner_session_id: str, stored_sha256: str) -> StoredImage | None:
        for path in self.metadata_root.glob("*.json"):
            record = self._load_record(path)
            if (
                record.expires_at_epoch > self.clock()
                and hmac.compare_digest(record.owner_session_hash, _owner_hash(owner_session_id))
                and hmac.compare_digest(record.stored_sha256, stored_sha256)
            ):
                return record
        return None

    def store(self, payload: bytes, *, content_type: str, owner_session_id: str) -> StoredImage:
        if not payload:
            raise UploadError("EMPTY_UPLOAD", "Image body is empty")
        if len(payload) > self.max_upload_bytes:
            raise UploadError("UPLOAD_TOO_LARGE", "Image exceeds the configured byte limit", 413)
        clean, source_format, width, height = self._decode_and_sanitize(payload, content_type)
        if len(clean) > self.max_upload_bytes:
            raise UploadError(
                "SANITIZED_IMAGE_TOO_LARGE",
                "Sanitized image exceeds the configured byte limit",
                413,
            )
        source_sha256 = hashlib.sha256(payload).hexdigest()
        stored_sha256 = hashlib.sha256(clean).hexdigest()
        now = self.clock()

        with self._lock:
            self._ensure_roots()
            duplicate = self._find_duplicate(owner_session_id, stored_sha256)
            if duplicate is not None:
                return StoredImage(**{**asdict(duplicate), "deduplicated": True})

            upload_id = str(uuid4())
            stored_name = f"{upload_id}.png"
            blob_path = self._safe_path(self.blob_root, stored_name)
            metadata_path = self._metadata_path(upload_id)
            temporary_blob = self._safe_path(self.blob_root, f".{upload_id}.tmp")
            temporary_metadata = self._safe_path(self.metadata_root, f".{upload_id}.tmp")
            record = StoredImage(
                upload_id=upload_id,
                owner_session_hash=_owner_hash(owner_session_id),
                source_format=source_format,
                source_sha256=source_sha256,
                stored_sha256=stored_sha256,
                stored_name=stored_name,
                width=width,
                height=height,
                encoded_bytes=len(clean),
                created_at_epoch=now,
                expires_at_epoch=now + self.ttl_seconds,
            )
            try:
                with temporary_blob.open("xb") as target:
                    target.write(clean)
                    target.flush()
                    os.fsync(target.fileno())
                temporary_metadata.write_text(
                    json.dumps(asdict(record), separators=(",", ":"), sort_keys=True),
                    encoding="utf-8",
                    newline="\n",
                )
                os.replace(temporary_blob, blob_path)
                os.replace(temporary_metadata, metadata_path)
            except OSError:
                temporary_blob.unlink(missing_ok=True)
                temporary_metadata.unlink(missing_ok=True)
                blob_path.unlink(missing_ok=True)
                raise
            return record

    def read(self, upload_id: str, *, owner_session_id: str) -> tuple[StoredImage, bytes]:
        with self._lock:
            record = self._owned_record(upload_id, owner_session_id)
            path = self._safe_path(self.blob_root, record.stored_name)
            try:
                payload = path.read_bytes()
            except OSError as error:
                raise UploadError("STORAGE_CORRUPT", "Stored image is unavailable", 500) from error
            if not hmac.compare_digest(hashlib.sha256(payload).hexdigest(), record.stored_sha256):
                raise UploadError(
                    "STORAGE_CORRUPT", "Stored image failed integrity validation", 500
                )
            return record, payload

    def delete(self, upload_id: str, *, owner_session_id: str) -> None:
        with self._lock:
            record = self._owned_record(upload_id, owner_session_id)
            self._safe_path(self.blob_root, record.stored_name).unlink(missing_ok=True)
            self._metadata_path(upload_id).unlink(missing_ok=True)

    def cleanup_expired(self) -> int:
        removed = 0
        with self._lock:
            self._ensure_roots()
            for path in self.metadata_root.glob("*.json"):
                record = self._load_record(path)
                if record.expires_at_epoch <= self.clock():
                    self._safe_path(self.blob_root, record.stored_name).unlink(missing_ok=True)
                    path.unlink(missing_ok=True)
                    removed += 1
        return removed
