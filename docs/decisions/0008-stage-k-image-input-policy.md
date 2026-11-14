# ADR-0008 — Stage K image-input policy

- Status: **ACCEPTED**
- Date: **15/11/2026**
- Scope: dual-chart image contract before secure upload/OCR implementation

## Decision

Lock image-input v1 to PNG/JPEG/WebP, 10 MiB, 800–4096 px width, 600–4096 px height and at most
16,777,216 decoded pixels. Require a usable 720×480 chart ROI, 60 closed 1H candles and 80 closed
15m candles. Symbol/timeframe contradictions reject input; temporal/market-context uncertainty fails
safe to `NO_TRADE`.

User metadata expresses intent. OCR at confidence ≥0.90 may prove a conflict but never silently
changes that intent. Live images older than 120 seconds, pair capture delta above 120 seconds or
last-price deviation above 0.35% cannot produce an actionable signal.

## Consequences

- Stage L has precise independent byte/dimension/pixel limits for secure decoding.
- Stage M receives a semantic golden set, not preselected algorithm thresholds.
- 12 pairs/24 deterministic fixtures cover valid dark/light/alternate themes and required failures.
- Two blind reordered review passes achieved 100% verdict/reason agreement and Cohen’s κ `1.00`,
  exceeding the locked 90%/0.80 gate.
- Synthetic examples do not establish real-domain OCR/quality performance; Stage M must measure it.
- All artifacts are generated locally with standard-library code; new cash cost remains **0 VNĐ**.

Evidence: `docs/IMAGE_SPEC.md`, `docs/IMAGE_CAPTURE_GUIDE.md`, `tests/fixtures/images/`,
`tests/image_contract/` and `reports/image-rubric.md`.
