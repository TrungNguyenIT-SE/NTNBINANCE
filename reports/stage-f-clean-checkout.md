# Stage F clean-checkout verification

> Verification date: `13/11/2026` (Asia/Saigon)
>
> Verified commit: `94fe5dc`
>
> Worktree: `D:\BINANCE\temp\stage-f-clean-20261113`
>
> Result: **PASS**

## Procedure

1. Created a detached Git worktree directly from the Stage F commit.
2. Ran `scripts/setup.ps1` without copying the primary workspace `.venv`, `node_modules` or runtime data.
3. Installed every Python package from `requirements.lock`, including `duckdb==2.0.0`.
4. Installed the local package in editable mode and installed frontend packages from the npm lockfile.
5. Ran `scripts/smoke.ps1`.
6. Ran `scripts/quality.ps1`.

## Results

```text
backend-smoke: PASS
frontend-smoke: PASS
stage-c-smoke: PASS

Ruff lint: PASS
Ruff format: PASS
mypy strict: PASS
pip check: PASS
pytest: 114 passed
statement + branch coverage: 91.09%
frontend ESLint/Prettier/TypeScript/Vitest/Vite build: PASS
npm audit during setup: 0 vulnerabilities
```

This confirms that Stage F can be rebuilt and verified from committed files alone. The test worktree contains no copied Binance raw/clean data, so reproducibility of the software environment is demonstrated separately from the local content-addressed dataset evidence in [`data-quality.md`](data-quality.md).
