# Stage N clean-checkout verification

- Date: 16/11/2026 (Asia/Saigon)
- Verified commit: `0aa9ab2`
- Clean worktree: `temp/stage-n-clean-20261116`
- Result: **PASS**

## Procedure and boundary

Created a detached worktree from the committed Stage N implementation, installed only the pinned
Python/npm lockfiles with `scripts/setup.ps1`, then ran `scripts/quality.ps1`. The clean checkout does
not contain Git-ignored market data; reproducible unit/contract tests use hand-calculated fixtures. The
real-data stability audit is preserved as committed `reports/feature-ablation.json`, bound to clean run
`13f11d10018f9914`, and can be regenerated only where that immutable local run exists.

## Results

- Ruff lint/format: PASS
- mypy strict: PASS across 121 source files
- `pip check`: PASS
- pytest: **251 passed**
- statement + branch coverage: **90.78%** (gate ≥90%)
- feature tests: **15 passed**, including all-vector future isolation
- frontend ESLint/Prettier/TypeScript: PASS
- frontend Vitest: **5 passed**
- frontend production build: PASS

No untracked source module, global Python package, paid API, cloud service or FINAL_HOLDOUT target is
needed for the Stage N quality gate.
