# Stage L secure-upload acceptance report

> Validation date: `16/11/2026` (Asia/Saigon)
>
> Result: **PASS**

## Scope

The review exercised the raw-body upload API, decoder/sanitizer, UUID storage, owner boundary,
rate limiter and expiration cleanup. Tests use local temporary directories and never contact an
external service.

## Acceptance matrix

| Threat/control | Evidence | Result |
|---|---|---|
| Oversized declared body | `Content-Length` above limit rejected before stream starts | PASS |
| Oversized chunked/unknown body | Streaming counter aborts on the crossing chunk | PASS |
| Compressed HTTP body | Non-identity `Content-Encoding` rejected | PASS |
| Fake MIME/signature | PNG declared JPEG and unsupported GIF rejected | PASS |
| Corrupt/truncated image | Valid-looking PNG prefix with broken payload fails decode | PASS |
| Decompression/pixel bomb | 900×700 input rejected against lower test pixel ceiling before load | PASS |
| Dimensions | 100×100 image rejected by locked envelope | PASS |
| Format coverage | Real PNG/JPEG/WebP decode and canonicalize to PNG | PASS |
| Animation | Two-frame WebP rejected | PASS |
| Metadata privacy | JPEG EXIF description absent after PNG re-encode | PASS |
| Filename traversal | `../../outside/secret.jpg` ignored and never stored | PASS |
| Route traversal | Encoded `../../outside` route cannot read/write outside storage | PASS |
| Stored-path tamper | Sidecar `../../outside.png` fails root containment | PASS |
| UUID naming | Only server UUID `.png` names appear in blob directory | PASS |
| Outside web root | Constructor rejects any storage/web-root overlap | PASS |
| IDOR read/delete | Foreign session receives indistinguishable 404 | PASS |
| Duplicate isolation | Same owner reuses ID; another owner receives a separate ID | PASS |
| Owner-token privacy | Sidecar contains SHA-256 owner hash, not the session value | PASS |
| Blob integrity | Modified bytes fail SHA-256 verification | PASS |
| Sidecar integrity | Invalid JSON fails closed | PASS |
| Rate limit | Third attempt after a 2/request test limit returns 429 + Retry-After | PASS |
| TTL cleanup | Expired blob and metadata are removed together | PASS |

## Locked runtime behavior

- Endpoint: `POST /api/v1/uploads/images`, raw body only.
- Read/delete: owner-scoped UUID routes; foreign/malformed/expired IDs return 404.
- Default rate: 10 attempts per session per 60 seconds.
- Retention: 2,592,000 seconds (30 days).
- Storage: `var/<profile>/uploads/{blobs,metadata}`, never mounted as static content.
- Input limits: profile byte ceiling up to 10 MiB, 800×600–4096×4096, max 16,777,216 pixels.
- Output: single-frame RGB PNG, metadata omitted, output byte ceiling rechecked.

## Automated verification

```text
secure-upload tests: 20 passed
full Python suite: 201 passed
statement + branch coverage: 90.97%
Ruff lint/format: PASS
mypy strict: PASS
pip check: PASS
Pillow decoder features: JPEG=true, WebP=true, zlib=true
```

## Exit Gate L

No API field controls a filesystem path. The original filename is ignored; server identifiers are
canonical UUIDs and every derived path must remain below its fixed root. Owner A cannot read or delete
Owner B's object and receives the same 404 as an unknown object. Tests also prove no traversal string
writes or changes an outside sentinel file. **Exit Gate L passes.**

## Residual risk

- Local session possession is not full authentication and must not be exposed to the public Internet.
- Pillow and its bundled codecs require ongoing advisory monitoring; Stage X repeats dependency audit.
- This stage validates file safety, not chart/OCR correctness, malware scanning or model suitability.
- In-memory rate state resets on restart, appropriate only for the locked single-worker local MVP.

All work uses local CPU/storage and an MIT-CMU library. New cash cost remains **0 VNĐ**.
