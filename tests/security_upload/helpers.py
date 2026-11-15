from __future__ import annotations

import io
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from PIL import Image

from ntnbinance.config import Settings, load_settings
from ntnbinance.main import create_app

ROOT = Path(__file__).resolve().parents[2]
VALID_PNG = (ROOT / "tests/fixtures/images/k01_1h.png").read_bytes()
OWNER = "session-owner-0001"
OTHER = "session-other-0002"


def image_bytes(
    format_name: str, *, size: tuple[int, int] = (960, 640), exif: bool = False
) -> bytes:
    output = io.BytesIO()
    image = Image.new("RGB", size, (12, 34, 56))
    kwargs: dict[str, object] = {}
    if exif:
        metadata = Image.Exif()
        metadata[0x010E] = "sensitive description"
        kwargs["exif"] = metadata
    image.save(output, format=format_name, **kwargs)
    return output.getvalue()


def settings(tmp_path: Path, **changes: Any) -> Settings:
    base = replace(load_settings("local-test"), runtime_root=tmp_path / "runtime")
    return replace(base, **changes)


def client(tmp_path: Path, **changes: Any) -> TestClient:
    return TestClient(create_app(settings(tmp_path, **changes)))


def upload(
    active: TestClient,
    payload: bytes = VALID_PNG,
    *,
    session: str = OWNER,
    content_type: str = "image/png",
    filename: str | None = None,
) -> Any:
    headers = {"X-Session-ID": session, "Content-Type": content_type}
    if filename is not None:
        headers["X-File-Name"] = filename
    return active.post("/api/v1/uploads/images", content=payload, headers=headers)
