# Stage K clean-checkout verification

> Verification date: `15/11/2026` (Asia/Saigon)
>
> Verified commit: `7aeca7e`
>
> Worktree: `D:\BINANCE\temp\stage-k-clean-20261115`
>
> Result: **PASS**

## Procedure

1. Created a detached worktree from the Stage K implementation commit.
2. Ran `scripts/setup.ps1` without copying the primary `.venv` or `node_modules`.
3. Regenerated all 24 PNG fixtures with the committed standard-library generator.
4. Verified no tracked file changed and recomputed the manifest checksum.
5. Ran the 16 image-contract tests and the complete `scripts/quality.ps1` gate.

## Results

```text
golden fixtures: 24 images / 12 pairs
manifest SHA-256: f1c61846bdfa12f9218156e7d12d7fdd3a1587e8daee6cdd37476498d3281107
deterministic regeneration: PASS (clean git worktree)
image-contract tests: 16 passed
review verdict agreement: 100%
Cohen's kappa: 1.00
Ruff lint/format: PASS
mypy strict: PASS
pip check: PASS
pytest: 176 passed
statement + branch coverage: 90.72%
frontend ESLint/Prettier/TypeScript/Vitest/Vite build: PASS
npm audit during setup: 0 vulnerabilities
```

This verifies installation, deterministic fixture generation, review evidence and all automated gates
without relying on the primary environment. The golden set is intentionally synthetic; real-domain
image/OCR performance remains a Stage M responsibility.

No paid service, API key, cloud compute, licensed image pack or new hardware is required. New cash
cost remains **0 VNĐ**.
