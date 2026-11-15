# Secure image upload v1

> Stage: L
>
> Status: `LOCKED`
>
> Runtime scope: local loopback API; research images only

## 1. Security boundary

The endpoint accepts one image per request as the raw HTTP body. It deliberately does not parse
multipart form data, archives, URLs, data URIs or base64 JSON. A 1H/15m pair will therefore be two
separate owner-scoped uploads, joined by a later prediction request.

```text
untrusted request
  → session + local rate gate
  → Content-Length precheck
  → streaming byte counter
  → Content-Encoding/MIME/magic checks
  → Pillow header + single-frame + dimension/pixel checks
  → verify + full decode
  → EXIF orientation normalization
  → RGB PNG re-encode with EXIF/ICC/XMP omitted
  → atomic UUID-named write under var/<profile>/uploads
  → owner-hash metadata sidecar
```

The API never uses a client filename as a path. `X-File-Name`, if sent by an older client, is ignored
and never persisted.

## 2. API contract

### Upload

```http
POST /api/v1/uploads/images
X-Session-ID: <16–64 characters: letters, digits, underscore, hyphen>
Content-Type: image/png | image/jpeg | image/webp

<raw image bytes>
```

Success is `201` with `upload_id`, canonical PNG SHA-256, dimensions, encoded byte count, timestamps
and `deduplicated`. The response never exposes a filesystem path or owner token.

### Read/delete

```http
GET    /api/v1/uploads/images/{uuid}
DELETE /api/v1/uploads/images/{uuid}
X-Session-ID: <same owner token>
```

Read returns canonical `image/png` with `Cache-Control: no-store` and
`X-Content-Type-Options: nosniff`. Delete returns `204`. A missing, malformed, expired or foreign ID
always returns the same `404 UPLOAD_NOT_FOUND`, preventing an ownership/existence oracle.

The session header is an owner-possession boundary for the local MVP, not Internet-grade login.
Public hosting and multi-user authentication remain outside the approved scope. Stage R must issue
high-entropy session tokens rather than user-chosen identifiers.

## 3. Locked controls

| Control | v1 behavior |
|---|---|
| Encoded request size | Profile limit, hard ceiling 10 MiB |
| Early rejection | Oversized declared `Content-Length` rejected before `request.stream()` |
| Unknown/chunked length | Count each chunk; abort immediately above limit |
| Content encoding | Only identity; compressed HTTP bodies rejected |
| Accepted image types | PNG, JPEG, WebP with MIME, magic and decoder agreement |
| Frames | Exactly one; animation/multi-frame rejected |
| Dimensions | 800×600 minimum, 4096 px maximum edge |
| Decoded pixels | At most 16,777,216; checked before full pixel load |
| Truncation | Pillow truncated-image loading remains disabled |
| Metadata | EXIF orientation applied; EXIF/XMP/ICC/text not copied to output |
| Canonical output | RGB PNG; output must also remain within encoded byte limit |
| Filename | Server UUID only; no original filename stored |
| Publication | Atomic temporary write + `os.replace` inside storage root |
| Integrity | Stored SHA-256 verified on every read |
| Duplicate | Idempotent only within the same owner; never shares an ID across owners |
| Rate limit | 10 upload attempts/session/60 seconds by default |
| Retention | 30 days; expired blob and metadata removed together |

Pillow's own decompression-bomb warnings/errors are converted into safe validation errors. The lower
project pixel ceiling is checked independently because the library default is not the product limit.

## 4. Storage layout and traversal defense

```text
var/<profile>/uploads/
├── blobs/<uuid>.png
└── metadata/<uuid>.json
```

This directory is outside `apps/web` and no static route mounts it. All identifiers are parsed as
canonical UUIDs, all derived paths are resolved and proven relative to their expected root, and
metadata stores only SHA-256 of the owner session. A tampered blob, sidecar or stored path fails
closed as `STORAGE_CORRUPT`/`STORAGE_PATH_INVALID`.

Cleanup is invoked before a successful new upload and is also exposed as the store's
`cleanup_expired()` operation for a future local scheduler. It deletes only validated UUID-derived
files inside the two upload subdirectories; it never recursively deletes a caller-selected path.

## 5. Error classes

| HTTP | Representative codes |
|---:|---|
| 400 | `MIME_NOT_ALLOWED`, `MAGIC_INVALID`, `MIME_MAGIC_MISMATCH`, `IMAGE_DECODE_FAILED`, `DIMENSIONS_INVALID`, `ANIMATED_IMAGE` |
| 401 | `SESSION_INVALID` |
| 404 | `UPLOAD_NOT_FOUND` |
| 413 | `UPLOAD_TOO_LARGE`, `PIXEL_LIMIT_EXCEEDED`, `SANITIZED_IMAGE_TOO_LARGE` |
| 429 | `RATE_LIMITED` plus `Retry-After` |
| 500 | `STORAGE_CORRUPT`, `STORAGE_PATH_INVALID` |

Detailed decoder exceptions, local paths, session values and original filenames are not returned.

## 6. Reproduction

```powershell
.venv\Scripts\pytest.exe tests\security_upload --no-cov
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\quality.ps1
```

Implementation evidence is in `src/ntnbinance/uploads/`; adversarial tests and the acceptance matrix
are in `tests/security_upload/` and `reports/upload-security.md`.

## 7. Limitations and next stages

- v1 is safe local storage, not malware scanning or content moderation.
- The endpoint does not prove the picture is a candlestick chart; visual/OCR quality belongs to M.
- The owner token is not a user account or authentication protocol; public deployment is forbidden.
- Rate state is in memory and intentionally single-worker, matching the local Stage C profile.
- OS-level compromise or a privileged local user can modify files; integrity checks detect but do not
  prevent such modification.

No paid service, cloud storage, antivirus API or commercial codec is required. New cash cost is
**0 VNĐ**.
