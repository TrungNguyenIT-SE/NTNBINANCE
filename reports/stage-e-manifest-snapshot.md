# Stage E raw manifest snapshot

Captured: `11/11/2026` (Asia/Saigon)
Raw data location: local `data/raw` (Git-ignored)
Audit result: `PASS`

## Integrity anchors

| Artifact | SHA-256 | Size / lines |
|---|---|---:|
| `data/raw/manifest.jsonl` | `6b68057e9780a88e18b7a25737cf04d5309b7c03f9241a95d50339805b4bba29` | 11,678 bytes / 26 entries |
| `data/raw/identity-index.txt` | `db05f443ced1d3443c955ce23993ce3388e407a735f856e9b02b156a3b524790` | 600,080 bytes / 9,232 identities |

## Audited counts

| Dataset | Records |
|---|---:|
| `trade_klines` | 2,886 |
| `mark_price_klines` | 2,882 |
| `index_price_klines` | 2,882 |
| `open_interest` | 576 |
| `funding_rates` | 6 |
| **Total** | **9,232** |

The 2,882 candle records per reference-price dataset are 2 × 1,440 from the first 24-hour REST run plus one new minute per symbol from the immediate rerun. Trade klines include those 2,882 REST records plus four final WebSocket events captured across two minute boundaries for both symbols.

This snapshot contains hashes and counts only. Raw market payloads remain local and are excluded from Git by policy.
