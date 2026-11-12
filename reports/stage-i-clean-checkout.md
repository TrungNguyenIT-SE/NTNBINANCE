# Stage I clean-checkout verification

> Verification date: `13/11/2026` (Asia/Saigon)
>
> Verified commit: `2eeba5e`
>
> Worktree: `D:\BINANCE\temp\stage-i-clean-20261113`
>
> Result: **PASS**

## Procedure

1. Created a detached worktree from the Stage I implementation commit.
2. Ran `scripts/setup.ps1` without copying the primary `.venv`, `node_modules` or runtime datasets.
3. Installed the complete Python lock, including official CPython 3.14 wheels for scikit-learn and
   XGBoost CPU; `npm ci` reported zero vulnerabilities.
4. Recomputed the committed baseline artifact checksum.
5. Verified the packaged `ntnbinance-baselines` CLI and installed model-library versions.
6. Ran the complete `scripts/quality.ps1` gate.

## Results

```text
baseline artifact checksum: PASS
artifact SHA-256: 8c56c1b6a80fb1a5edf22185a337fbfe9967cc00d2b0fdc08035951771e4cbcf
baseline CLI packaging/help: PASS
scikit-learn: 1.9.1
xgboost: 3.4.1 (CPU distribution)
Ruff lint/format: PASS
mypy strict: PASS
pip check: PASS
pytest: 148 passed
statement + branch coverage: 91.08%
frontend ESLint/Prettier/TypeScript/Vitest/Vite build: PASS
npm audit during setup: 0 vulnerabilities
```

The clean checkout intentionally contains no ignored Stage F clean candles or Stage G label rows, so
it verifies installation, packaging, artifact identity and tests independently. The live workspace
separately reproduced baseline run `f9134abdb58bc0d4` twice with identical artifact SHA-256 while
skipping 26 sealed FINAL_HOLDOUT targets before JSON target deserialization.

No paid service, API key, cloud compute or new hardware is required. New cash cost remains **0 VNĐ**.
