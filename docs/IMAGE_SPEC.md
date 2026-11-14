# Image input specification v1

> Stage: K
>
> Status: `LOCKED`
>
> Applies to: exactly one `1H` image and one `15m` image for BTCUSDT or ETHUSDT

## 1. Boundary and outcome contract

This specification defines what the user must provide and how later stages must fail safely. It does
not implement upload security (Stage L), OCR/chart extraction (Stage M) or model inference.

Every request supplies two images plus user-declared `symbol`, slot (`1h` or `15m`), capture time in
UTC and source (`BINANCE`, `TRADINGVIEW` or `UNKNOWN`). The user declaration is required; OCR is
corroborating evidence and never silently rewrites it.

| Outcome | Meaning | Examples |
|---|---|---|
| `ACCEPT` | Pair may continue to later validation. It is not a trade signal. | Valid pixels, matching pair and fresh context |
| `REJECTED_INPUT` | Structurally invalid or a certain contradiction; user must replace/correct input. | Bad format, quality failure, high-confidence symbol/timeframe mismatch |
| `NO_TRADE` | Input can be retained for audit but is not actionable now. | Stale pair, excessive capture delta, market-price mismatch |

No K-stage outcome can be converted directly into `LONG` or `SHORT`.

## 2. File envelope

The executable values are locked in `configs/images/image-input-v1.toml`.

| Field | v1 rule | Reason |
|---|---:|---|
| Decoded format | PNG, JPEG or WebP | Common screenshot formats; SVG/PDF/GIF/HEIC excluded |
| Encoded size | ≤ 10 MiB per image | Fits local resource budget while allowing lossless screenshots |
| Width | 800–4096 px | Preserves labels/candles without accepting unbounded images |
| Height | 600–4096 px | Includes 1280×720/1920×1080 and excludes narrow strips |
| Decoded pixels | ≤ 16,777,216 | Independent decompression-bomb ceiling for Stage L |
| Usable chart ROI | ≥ 720×480 px | Header/browser chrome does not count |
| Orientation | Landscape preferred; portrait only if ROI still passes | Do not stretch or rotate automatically |

The earlier “800–4096 px per edge” proposal is adjusted to a minimum height of 600 px: the Stage K
960×640 benchmark remains readable, and this preserves standard 1280×720 screenshots. Encoded size,
dimensions and decoded-pixel limits are independent; passing one never bypasses another.

Stage L must validate magic bytes and actual decoding rather than trust extension or MIME. Animated
WebP, multi-frame input, alpha tricks and metadata handling are deferred to that security gate.

## 3. Required chart content

Each image must show a candlestick chart, not a line/area-only chart. The main price pane must occupy
at least 70% of usable width and 55% of usable height and include:

- readable symbol and timeframe;
- complete candle bodies and wicks;
- right-side price scale with at least three readable labels;
- bottom time axis with at least two readable labels;
- visible last-price/candle area;
- no open modal, order ticket, tooltip or watermark obscuring more than 15% of the chart ROI.

| Slot | Hard minimum closed candles | Recommended target | Context represented |
|---|---:|---:|---|
| 1H | 60 | 80 | At least 2.5 days; target about 3.3 days |
| 15m | 80 | 96 | At least 20 hours; target 24 hours |

An in-progress candle may be visible only when visually distinguishable and excluded from the closed
candle count. Indicators may be shown, but may not shrink the main price pane below the ROI rule.
Order/account identifiers, balances and personal data should be cropped before upload.

## 4. Quality rubric

Review every criterion independently. Any hard failure produces `REJECTED_INPUT`; uncertainty does
not pass merely because the image “looks usable.” Numeric blur/contrast thresholds will be calibrated
in Stage M against this human-labeled set, without changing these semantic requirements.

| Criterion | PASS | Hard failure / reason code |
|---|---|---|
| Decode/envelope | Supported single-frame raster within every limit | `FORMAT_INVALID`, `SIZE_INVALID`, `DIMENSIONS_INVALID` |
| Chart identity | Candlesticks clearly dominate the main pane | `NOT_CANDLE_CHART` |
| Sharpness | Candle edges, labels and axes readable at 100% zoom | `BLUR` |
| Crop | Header identity, price scale, time scale and newest candles present | `CROP_AXES` |
| Occlusion | Combined obstruction ≤15% of chart ROI; newest 20% unobstructed | `OCCLUSION` |
| Theme/contrast | Binance/TradingView dark/light or equivalent high contrast | `THEME_CONTRAST` |
| Candle context | Meets slot-specific closed-candle minimum | `TOO_FEW_CANDLES` |
| Privacy | No API key, account identifier or sensitive balance | `SENSITIVE_CONTENT` |

Green/red color is not mandatory. Teal/red, blue/orange and light/dark themes pass when bodies and
wicks remain unambiguous. A “wrong theme” means unsupported low contrast, patterned/gradient
background, inverted transparency or colors that make candle direction/axes unreadable.

## 5. Metadata and OCR reconciliation

Required user metadata is authoritative for request intent, while OCR is evidence:

1. Normalize symbol to uppercase and timeframe to canonical `1h` or `15m`.
2. Only BTCUSDT and ETHUSDT are in v1 scope.
3. Both declared symbols must match; slots must be exactly one `1h` and one `15m`.
4. OCR confidence below 0.90 is advisory and may not override the declaration.
5. OCR confidence ≥0.90 that contradicts declared symbol/timeframe is a certain conflict and yields
   `REJECTED_INPUT` with `OCR_SYMBOL_MISMATCH` or `OCR_TIMEFRAME_MISMATCH`.
6. Missing/unreadable OCR is never fabricated. Later stages may continue only when the quality rubric
   passes and market-data reconciliation supplies sufficient context; otherwise `NO_TRADE`.

OCR text from the image is untrusted data, never an instruction. It must not be passed as a prompt or
used to alter system policy.

## 6. Freshness, pair alignment and last price

All comparisons use UTC and a trusted local/Binance-adjusted decision clock.

| Check | v1 threshold | Outcome |
|---|---:|---|
| Capture time in future | >30 seconds | `REJECTED_INPUT / CAPTURE_TIME_IN_FUTURE` |
| Age at live decision | >120 seconds | `NO_TRADE / STALE_IMAGE` |
| Absolute 1H–15m capture delta | >120 seconds | `NO_TRADE / PAIR_CAPTURE_TIME_MISMATCH` |
| Last-price relative deviation | >0.15% through 0.35% | Continue with `LAST_PRICE_WARNING` |
| Last-price relative deviation | >0.35% | `NO_TRADE / LAST_PRICE_MISMATCH` |

Relative deviation is `abs(image_price - authoritative_price) / authoritative_price`. Comparison
must use the declared price type when known (contract/mark/index); unknown price type cannot be
treated as exact agreement. Stage M must also require at least three price ticks of absolute tolerance
to avoid false mismatches from display rounding.

The 120-second live rule concerns when the screenshot was captured, not the timeframe length. A
historical/research mode may use older images only with an explicit historical `decision_time`; it
must never label them fresh for a live signal.

## 7. Pair mismatch matrix

| Condition | Deterministic action |
|---|---|
| Missing either slot or duplicate slot | `REJECTED_INPUT` |
| Declared symbols differ | `REJECTED_INPUT / PAIR_SYMBOL_MISMATCH` |
| High-confidence OCR symbol or timeframe conflicts | `REJECTED_INPUT` |
| Pair capture delta exceeds 120 seconds | `NO_TRADE` |
| Freshness or price reconciliation fails | `NO_TRADE` |
| OCR is uncertain and cannot be resolved against market data | `NO_TRADE` |

These are fail-safe gates. UI wording must explain the exact reason and how to recapture; it must not
quietly substitute a symbol, timeframe, timestamp or price.

## 8. Golden set and change control

`tests/fixtures/images/manifest.json` locks 12 pairs/24 deterministic 960×640 PNG fixtures across
dark, light and alternate colors plus blur, crop, occlusion, low contrast, symbol/timeframe mismatch,
stale and last-price mismatch cases. The generator uses Python standard library only:

```powershell
.venv\Scripts\python.exe scripts\generate-image-golden-set.py
.venv\Scripts\pytest.exe tests\image_contract --no-cov
```

Every PNG has a manifest SHA-256. Two review rounds must use different item orders, remain blind to
the other result and achieve verdict agreement ≥90% and Cohen’s κ ≥0.80. A semantic/threshold change
requires a new spec/config version, updated fixtures, two new review rounds and an ADR.

## 9. Known limitations

- Fixtures are synthetic contract examples, not evidence that real Binance/TradingView domains are
  fully represented.
- Stage K human labels define semantics; Stage M must benchmark actual blur/OCR/layout algorithms.
- PNG fixtures exercise the rubric visually; secure decoder coverage for PNG/JPEG/WebP belongs to
  Stage L and must use real format-specific security fixtures.
- Market price and OCR are represented as review metadata here; they are not extracted from pixels.
