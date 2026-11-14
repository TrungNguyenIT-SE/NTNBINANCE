# Stage J clean-checkout verification

> Verification date: `15/11/2026` (Asia/Saigon)
>
> Verified commit: `7482630`
>
> Worktree: `D:\BINANCE\temp\stage-j-clean-20261115`
>
> Result: **PASS**

## Procedure

1. Created a detached worktree from the Stage J implementation commit.
2. Ran `scripts/setup.ps1` without copying the primary `.venv`, `node_modules` or runtime datasets.
3. Verified the committed backtest artifact checksum.
4. Verified the packaged `ntnbinance-backtest` CLI and its documented arguments.
5. Ran the complete `scripts/quality.ps1` gate.

## Results

```text
backtest artifact checksum: PASS
artifact SHA-256: a322b0d8e58db2a1f55eee963f00da2894402c4931e78ab79e1e753fb23956ec
backtest CLI packaging/help: PASS
Ruff lint/format: PASS
mypy strict: PASS
pip check: PASS
pytest: 160 passed
statement + branch coverage: 90.48%
frontend ESLint/Prettier/TypeScript/Vitest/Vite build: PASS
npm audit during setup: 0 vulnerabilities
```

The clean checkout intentionally contains no ignored raw or clean runtime market dataset. It proves
installation, CLI packaging, committed artifact identity and all automated tests independently. The
live workspace separately executed the locked validation backtest twice with identical run ID
`efac5d1adcec0a1c` and identical artifact SHA-256 while FINAL_HOLDOUT remained sealed.

No paid service, API key, cloud compute or new hardware is required. New cash cost remains **0 VNĐ**.
