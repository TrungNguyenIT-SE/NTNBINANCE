# Stage G clean-checkout verification

> Verification date: `13/11/2026` (Asia/Saigon)
>
> Verified commit: `a2c6345`
>
> Worktree: `D:\BINANCE\temp\stage-g-clean-20261113`
>
> Result: **PASS**

## Procedure

1. Created a detached worktree from the Stage G implementation commit.
2. Ran `scripts/setup.ps1` without copying `.venv`, `node_modules`, raw, clean or label artifacts.
3. Confirmed the installed `ntnbinance-labels` entry point exposes the documented CLI.
4. Ran `scripts/smoke.ps1`.
5. Ran the complete `scripts/quality.ps1` gate.

## Results

```text
label CLI packaging/help: PASS
backend-smoke: PASS
frontend-smoke: PASS
stage-c-smoke: PASS
Ruff lint/format: PASS
mypy strict: PASS
pip check: PASS
pytest: 128 passed
statement + branch coverage: 90.33%
frontend ESLint/Prettier/TypeScript/Vitest/Vite build: PASS
npm audit during setup: 0 vulnerabilities
```

The clean checkout intentionally contains no Stage F market dataset, so the software rebuild proof is independent from the content-addressed live label-run evidence in [`label-distribution.md`](label-distribution.md).
