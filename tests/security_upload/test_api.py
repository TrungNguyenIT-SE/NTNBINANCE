from __future__ import annotations

import io
from pathlib import Path

from PIL import Image

from .helpers import OTHER, OWNER, VALID_PNG, client, image_bytes, upload


def test_upload_reencodes_strips_metadata_and_ignores_malicious_filename(tmp_path: Path) -> None:
    payload = image_bytes("JPEG", exif=True)
    with client(tmp_path) as active:
        response = upload(
            active,
            payload,
            content_type="image/jpeg",
            filename="../../outside/secret.jpg",
        )
        assert response.status_code == 201
        record = response.json()
        downloaded = active.get(
            f"/api/v1/uploads/images/{record['upload_id']}", headers={"X-Session-ID": OWNER}
        )

    assert record["source_format"] == "JPEG"
    assert record["deduplicated"] is False
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "image/png"
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    with Image.open(io.BytesIO(downloaded.content)) as clean:
        clean.load()
        assert clean.format == "PNG"
        assert not clean.getexif()
        assert "icc_profile" not in clean.info
        assert "secret" not in str(clean.info).lower()
    assert not (tmp_path / "outside").exists()
    stored = list((tmp_path / "runtime/uploads/blobs").glob("*"))
    assert [path.name for path in stored] == [f"{record['upload_id']}.png"]
    metadata = (tmp_path / "runtime/uploads/metadata" / f"{record['upload_id']}.json").read_text(
        encoding="utf-8"
    )
    assert OWNER not in metadata
    assert "secret.jpg" not in metadata


def test_owner_scope_hides_read_and_delete_from_other_session(tmp_path: Path) -> None:
    with client(tmp_path) as active:
        created = upload(active).json()
        path = f"/api/v1/uploads/images/{created['upload_id']}"
        assert active.get(path, headers={"X-Session-ID": OTHER}).status_code == 404
        assert active.delete(path, headers={"X-Session-ID": OTHER}).status_code == 404
        assert active.get(path, headers={"X-Session-ID": OWNER}).status_code == 200
        assert active.delete(path, headers={"X-Session-ID": OWNER}).status_code == 204
        assert active.get(path, headers={"X-Session-ID": OWNER}).status_code == 404


def test_duplicate_is_idempotent_per_owner_but_not_shared_across_owners(tmp_path: Path) -> None:
    with client(tmp_path) as active:
        first = upload(active).json()
        duplicate = upload(active).json()
        other = upload(active, session=OTHER).json()

    assert duplicate["upload_id"] == first["upload_id"]
    assert duplicate["deduplicated"] is True
    assert other["upload_id"] != first["upload_id"]
    assert len(list((tmp_path / "runtime/uploads/blobs").glob("*.png"))) == 2


def test_missing_or_malformed_session_is_unauthorized(tmp_path: Path) -> None:
    with client(tmp_path) as active:
        missing = active.post(
            "/api/v1/uploads/images",
            content=VALID_PNG,
            headers={"Content-Type": "image/png"},
        )
        malformed = upload(active, session="../../short")
    assert missing.status_code == 401
    assert malformed.status_code == 401


def test_mime_magic_corruption_and_dimension_failures_are_structured(tmp_path: Path) -> None:
    with client(tmp_path) as active:
        mismatch = upload(active, content_type="image/jpeg")
        corrupt = upload(active, b"\x89PNG\r\n\x1a\ncorrupt")
        small = upload(active, image_bytes("PNG", size=(100, 100)))

    assert mismatch.json()["detail"]["code"] == "MIME_MAGIC_MISMATCH"
    assert corrupt.json()["detail"]["code"] == "IMAGE_DECODE_FAILED"
    assert small.json()["detail"]["code"] == "DIMENSIONS_INVALID"


def test_png_jpeg_and_webp_decode_to_canonical_png(tmp_path: Path) -> None:
    samples = [
        (VALID_PNG, "image/png", "PNG"),
        (image_bytes("JPEG"), "image/jpeg", "JPEG"),
        (image_bytes("WEBP"), "image/webp", "WEBP"),
    ]
    with client(tmp_path) as active:
        results = [
            upload(active, payload, content_type=mime).json() for payload, mime, _ in samples
        ]
    assert [result["source_format"] for result in results] == [item[2] for item in samples]


def test_rate_limit_is_per_session_and_returns_retry_after(tmp_path: Path) -> None:
    with client(tmp_path, upload_rate_limit=2) as active:
        assert upload(active).status_code == 201
        assert upload(active).status_code == 201
        blocked = upload(active)
        assert upload(active, session=OTHER).status_code == 201
    assert blocked.status_code == 429
    assert blocked.json()["detail"]["code"] == "RATE_LIMITED"
    assert int(blocked.headers["retry-after"]) >= 1


def test_too_large_and_pixel_bomb_are_rejected(tmp_path: Path) -> None:
    with client(tmp_path, max_upload_bytes=len(VALID_PNG) - 1) as byte_limited:
        oversized = upload(byte_limited)
    with client(tmp_path / "pixels", max_image_pixels=600_000) as pixel_limited:
        too_many_pixels = upload(pixel_limited, image_bytes("PNG", size=(900, 700)))
    assert oversized.status_code == 413
    assert oversized.json()["detail"]["code"] == "UPLOAD_TOO_LARGE"
    assert too_many_pixels.json()["detail"]["code"] == "PIXEL_LIMIT_EXCEEDED"


def test_compressed_and_unsupported_content_types_are_rejected(tmp_path: Path) -> None:
    with client(tmp_path) as active:
        compressed = active.post(
            "/api/v1/uploads/images",
            content=VALID_PNG,
            headers={
                "Content-Encoding": "gzip",
                "Content-Type": "image/png",
                "X-Session-ID": OWNER,
            },
        )
        unsupported = upload(active, content_type="image/gif")
    assert compressed.json()["detail"]["code"] == "CONTENT_ENCODING_REJECTED"
    assert unsupported.json()["detail"]["code"] == "MIME_NOT_ALLOWED"


def test_animated_webp_is_rejected(tmp_path: Path) -> None:
    output = io.BytesIO()
    first = Image.new("RGB", (960, 640), "red")
    second = Image.new("RGB", (960, 640), "blue")
    first.save(
        output,
        format="WEBP",
        save_all=True,
        append_images=[second],
        duration=100,
        loop=0,
    )
    with client(tmp_path) as active:
        response = upload(active, output.getvalue(), content_type="image/webp")
    assert response.json()["detail"]["code"] == "ANIMATED_IMAGE"


def test_route_identifier_cannot_traverse_storage(tmp_path: Path) -> None:
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")
    with client(tmp_path) as active:
        response = active.get(
            "/api/v1/uploads/images/..%2F..%2Foutside",
            headers={"X-Session-ID": OWNER},
        )
    assert response.status_code in {404, 422}
    assert outside.read_bytes() == b"outside"


def test_non_uuid_identifier_is_hidden_as_not_found(tmp_path: Path) -> None:
    with client(tmp_path) as active:
        response = active.get(
            "/api/v1/uploads/images/not-a-uuid",
            headers={"X-Session-ID": OWNER},
        )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "UPLOAD_NOT_FOUND"
