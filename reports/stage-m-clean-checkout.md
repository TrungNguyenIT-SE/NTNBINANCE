# Stage M clean-checkout verification

- Date: 16/11/2026 (Asia/Saigon)
- Verified commit: `374b661`
- Clean worktree: `temp/stage-m-clean2-20261116` (ignored local verification directory)
- Result: **PASS**

## Procedure

1. Created a detached Git worktree from the committed Stage M implementation.
2. Verified `models/ocr/LICENSE.tessdata-fast` SHA-256 equals
   `CFC7749B96F63BD31C3C42B5C471BF756814053E847C10F3EB003417BC523D30`.
3. Ran `scripts/setup.ps1` from an empty environment; pinned Python and frontend dependencies installed.
4. Ran `scripts/quality.ps1` in that worktree.

## Results

- Ruff lint and formatting: PASS
- mypy strict (110 source files): PASS
- `pip check`: PASS
- pytest: **236 passed**
- branch-aware coverage: **91.43%** (gate ≥ 90%)
- frontend ESLint/Prettier/TypeScript: PASS
- frontend Vitest: **5 passed**
- frontend production build: PASS

The first verification worktree exposed CRLF conversion of the checksum-protected tessdata license on
Windows. The implementation did the intended fail-closed action. Commit `374b661` then added explicit
Git attributes (`eol=lf` for the license, binary for `*.traineddata`). A new worktree checked out the
expected bytes and passed every gate. No untracked source or local global dependency is required.
