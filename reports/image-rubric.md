# Stage K image-rubric validation

> Review date: `15/11/2026` (Asia/Saigon)
>
> Result: **PASS — image input specification v1 locked**

## Locked corpus

- 12 dual-image cases / 24 deterministic PNG fixtures.
- Resolution: 960×640 RGB; total encoded size: 229,633 bytes.
- Per-file encoded range: 3,021–10,454 bytes.
- Manifest SHA-256: `f1c61846bdfa12f9218156e7d12d7fdd3a1587e8daee6cdd37476498d3281107`.
- Generator: `scripts/generate-image-golden-set.py`, Python standard library only.
- Distribution: 4 `ACCEPT`, 6 `REJECTED_INPUT`, 2 `NO_TRADE`.

The 960×640 fixtures verified readable axes, labels, candles and failure overlays above the locked
720×480 chart ROI. Based on this review, v1 adjusts the provisional minimum from 800 px on every edge
to 800 px width and 600 px height, preserving common 1280×720 screenshots. The 10 MiB/file ceiling is
retained but paired with 4096×4096 and 16,777,216 decoded-pixel limits; Stage L must enforce all three.

## Case matrix

| Case | Theme/condition | Expected | Round A | Round B | Primary reason |
|---|---|---|---|---|---|
| K01 | BTC dark | ACCEPT | ACCEPT | ACCEPT | `VALID_DARK` |
| K02 | ETH light | ACCEPT | ACCEPT | ACCEPT | `VALID_LIGHT` |
| K03 | ETH alternate colors | ACCEPT | ACCEPT | ACCEPT | `VALID_ALT_COLORS` |
| K04 | BTC light | ACCEPT | ACCEPT | ACCEPT | `VALID_LIGHT` |
| K05 | Low-detail simulated blur | REJECTED_INPUT | REJECTED_INPUT | REJECTED_INPUT | `BLUR` |
| K06 | Price/time axes cropped | REJECTED_INPUT | REJECTED_INPUT | REJECTED_INPUT | `CROP_AXES` |
| K07 | Central order panel occlusion | REJECTED_INPUT | REJECTED_INPUT | REJECTED_INPUT | `OCCLUSION` |
| K08 | Unsupported low-contrast theme | REJECTED_INPUT | REJECTED_INPUT | REJECTED_INPUT | `THEME_CONTRAST` |
| K09 | BTC/ETH pair conflict | REJECTED_INPUT | REJECTED_INPUT | REJECTED_INPUT | `PAIR_SYMBOL_MISMATCH` |
| K10 | Duplicate 1H assignment | REJECTED_INPUT | REJECTED_INPUT | REJECTED_INPUT | `PAIR_TIMEFRAME_MISMATCH` |
| K11 | Capture older than live threshold | NO_TRADE | NO_TRADE | NO_TRADE | `STALE_IMAGE` |
| K12 | Last price beyond tolerance | NO_TRADE | NO_TRADE | NO_TRADE | `LAST_PRICE_MISMATCH` |

## Independent review gate

Round A reviewed K01→K12. Round B was a separate pass, blind to the Round A result and presented in
the fixed reordered sequence K08, K03, K11, K05, K01, K10, K12, K06, K04, K09, K02, K07. Both used
rubric v1 and recorded verdict plus primary reason before comparison.

| Measure | Required | Actual | Result |
|---|---:|---:|---|
| Pair coverage | 12 | 12 | PASS |
| Verdict agreement | ≥90% | 100% | PASS |
| Primary-reason agreement | ≥90% | 100% | PASS |
| Cohen's κ, three outcomes | ≥0.80 | 1.00 | PASS |

The automated regression test verifies both JSON review records, their different presentation order,
agreement, κ, image dimensions, PNG signature and every fixture SHA-256.

## Verification gates

- Image-contract suite: `16 passed`.
- Full Python suite: `176 passed`; statement + branch coverage: `90.72%`.
- Ruff, mypy strict, dependency consistency, ESLint, Prettier, TypeScript, Vitest and production
  build: `PASS`.
- Golden-set regeneration produced the identical manifest and identical per-image SHA-256 values.

## Thresholds locked by review

- Formats: PNG/JPEG/WebP; max 10 MiB each.
- Width 800–4096 px; height 600–4096 px; max 16,777,216 decoded pixels.
- Usable chart ROI at least 720×480 px.
- At least 60 closed candles for 1H and 80 for 15m; targets 80/96.
- Occlusion no more than 15% of chart ROI and never over the newest 20%.
- Live image age and pair capture delta no more than 120 seconds; future skew no more than 30 seconds.
- OCR conflicts become certain at confidence ≥0.90.
- Last-price warning above 0.15%; fail-safe `NO_TRADE` above 0.35% relative deviation.

## Reproduction

```powershell
.venv\Scripts\python.exe scripts\generate-image-golden-set.py
.venv\Scripts\pytest.exe tests\image_contract --no-cov
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\quality.ps1
```

## Limitations and next gate

This is a semantic golden set, not a performance claim for real-world OCR or blur detection. It does
not contain malicious decoders, real JPEG/WebP security cases, or private user screenshots. Stage L
must implement safe format validation; Stage M must calibrate pixel/OCR algorithms against real-domain
consented evaluation images without changing the final holdout or tuning to these expected answers.

No paid API, cloud service, licensed image pack or new hardware was used. New cash cost is **0 VNĐ**.
