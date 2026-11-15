# ADR-0009 — Stage L secure-upload policy

- Status: **ACCEPTED**
- Date: **16/11/2026**
- Scope: local image ingest, canonical storage and owner-scoped access

## Decision

Use a raw-body streaming endpoint rather than multipart for Stage L. Reject oversized declared bodies
before streaming and enforce the same ceiling while reading unknown/chunked lengths. Verify MIME,
magic bytes and Pillow decoder format; reject truncated, animated, corrupt, undersized and
pixel-excessive images.

Normalize EXIF orientation, convert to RGB and re-encode as PNG without carrying EXIF/XMP/ICC/text.
Store only UUID-named canonical files and owner-hash sidecars under `var/<profile>/uploads`, outside
the web root. Read/delete require the matching session possession token and hide foreign existence as
404. Apply a local per-session rate gate and 30-day expiration cleanup.

Pin `Pillow==13.0.0` from PyPI. The installed CPython 3.14 wheel exposes JPEG/WebP/zlib support,
contains its MIT-CMU license and adds no paid/runtime service dependency.

## Consequences

- Client filenames and path components never control local writes.
- Duplicate content is idempotent for one owner but does not create cross-owner access.
- Input metadata is intentionally discarded; future model stages operate on canonical pixels.
- Raw-body upload is simpler and safer but the UI must issue two requests instead of one multipart
  pair request.
- Local session possession is not sufficient for public multi-user hosting; that remains prohibited.
- New cash cost remains **0 VNĐ**.

Evidence: `docs/SECURE_UPLOAD.md`, `tests/security_upload/`, `reports/upload-security.md` and
`reports/stage-l-license-audit.md`.
