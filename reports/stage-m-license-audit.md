# Stage M dependency and license audit

- Audit date: 16/11/2026
- Scope: local OCR dependency and English language model
- Result: **APPROVED for the local zero-cost MVP**

| Artifact | Pin | License/evidence | Result |
|---|---|---|---|
| `tesserocr` | 2.13.0 CPython 3.14 Windows wheel | MIT wrapper; bundled runtime notices retained; Tesseract 5.5.4/Leptonica verified | APPROVED |
| Tesseract runtime | 5.5.4 inside wheel | Apache-2.0; runtime version verified locally | APPROVED |
| `eng.traineddata` | `tessdata_fast` commit `87416418657359cb625c412a48b6e1d6d41c29bd` | Apache-2.0; SHA-256 `7D4322BD2A7749724879683FC3912CB542F19906C83BCC1A52132556427170B2` | APPROVED |
| tessdata license | same commit | SHA-256 `CFC7749B96F63BD31C3C42B5C471BF756814053E847C10F3EB003417BC523D30` | RETAINED |

The model and license are committed under `models/ocr/`; `MANIFEST.json` records provenance and
checksums. Runtime verifies every checksum and fails closed on mismatch. The fetch script downloads
only pinned GitHub raw URLs and verifies hashes before replacement.

No paid key, subscription, cloud OCR, telemetry or runtime network call is required. Incremental cash
cost is **0 VNĐ**. Distribution packaging in Stage Z must retain all licenses shipped by the wheel.
