# Stage H clean-checkout verification

> Verification date: `13/11/2026` (Asia/Saigon)
>
> Verified commit: `e092301`
>
> Worktree: `D:\BINANCE\temp\stage-h-clean-20261113`
>
> Result: **PASS**

## Procedure

1. Created a detached worktree from the Stage H implementation commit.
2. Ran `scripts/setup.ps1` without copying the primary `.venv`, `node_modules` or runtime datasets.
3. Recomputed the committed split-manifest SHA-256 after checkout.
4. Confirmed the installed `ntnbinance-split` entry point exposes the documented CLI.
5. Ran `scripts/smoke.ps1` and `scripts/quality.ps1`.

## Results

```text
split manifest checksum: PASS
manifest SHA-256: 2d7a0a201d371418d2282db85c82dfa28ebb52e9a21e7548560c015e1922a0b2
split CLI packaging/help: PASS
backend/frontend/stage-c smoke: PASS
Ruff lint/format: PASS
mypy strict: PASS
pip check: PASS
pytest: 138 passed
statement + branch coverage: 91.21%
frontend ESLint/Prettier/TypeScript/Vitest/Vite build: PASS
npm audit during setup: 0 vulnerabilities
```

The clean checkout contains the label-blind split manifest but no raw, clean or label runtime dataset. This proves that membership/checksum evidence and leakage tests are independently rebuildable without opening final-holdout labels.
