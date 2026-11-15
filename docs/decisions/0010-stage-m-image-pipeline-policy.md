# ADR-0010 — Stage M fail-safe image pipeline

- Status: **ACCEPTED**
- Date: **16/11/2026**
- Scope: chart ROI, quality, local OCR, synthetic rendering and image-pair reconciliation

## Decision

Use Pillow, NumPy and SciPy for deterministic local chart detection and quality metrics. Use pinned
`tesserocr==2.13.0` with the official `tessdata_fast` English model whose commit and SHA-256 are kept
in the repository. OCR only the header and extract allow-listed fields without fuzzy correction.

Treat the image as untrusted evidence. Low quality/non-chart and confirmed identity mismatches are
`REJECTED_INPUT`; insufficient OCR evidence, stale captures, price mismatch and unknown layouts are
`NO_TRADE`. Never infer missing identity fields. Reuse the locked Stage K cross-image policy.

Generate synthetic research charts only from ordered, closed candles at or before decision time.
Allow image augmentation only in TRAIN and prohibit flips/time reversal. Lock the v1 thresholds before
the benchmark matrix and record them in `configs/images/image-pipeline-v1.toml`.

## Consequences

- Processing and OCR stay local and require no paid service or API key.
- Conservative rejection increases abstention but prevents silent symbol/timeframe contamination.
- Tesseract CPU latency is suitable for an asynchronous local MVP, not high-frequency inference.
- User-provided conversation images guide layout design but are not claimed as persistent test assets.
- New cash cost remains **0 VNĐ**.

Evidence: `docs/IMAGE_PIPELINE.md`, `tests/image_pipeline/`, `reports/image-pipeline.md` and
`reports/stage-m-license-audit.md`.
