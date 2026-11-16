# Stage O clean-checkout verification

- Date: 16/11/2026 (Asia/Saigon)
- Verified commit: `2344f69`
- Detached worktree: `D:\BINANCE-stage-o-verify`
- Result: **PASS**

## Procedure and boundary

Created a detached worktree from the committed Stage O implementation, installed only the pinned
Python and npm lockfiles with `scripts/setup.ps1`, then ran `scripts/quality.ps1`. The clean checkout
contained neither Git-ignored market data nor the local model-selection image cache. Unit and contract
tests use deterministic fixtures; the committed experiment artifact preserves the real local run's
input hashes and explicitly records that FINAL_HOLDOUT labels were not read.

The real-data model-selection run itself cannot be repeated from a public clean checkout because the
licensed/local market dataset is intentionally not committed. This verification establishes build and
test reproducibility, not independent reproduction of the recorded validation metrics.

## Results

- Ruff lint/format: PASS
- mypy strict: PASS across 130 source files
- `pip check`: PASS
- pytest: **261 passed**
- statement + branch coverage: **90.01%** (gate ≥90%)
- Stage O focused tests: **10 passed**
- frontend ESLint/Prettier/TypeScript: PASS
- frontend Vitest: **5 passed**
- frontend production build: PASS

No untracked source module, cloud service, paid API, FINAL_HOLDOUT target or model-selection cache was
required. New cash cost remained **0 VNĐ**.
