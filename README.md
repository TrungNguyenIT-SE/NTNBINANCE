# NTNBINANCE

Local/private research MVP for Binance USDⓈ-M perpetual signals from 1H + 15m chart images and point-in-time market data.

## Safety and scope

- Research and paper trading only.
- Output contract: `LONG / SHORT / NO_TRADE`.
- Supported symbols: `BTCUSDT`, `ETHUSDT`.
- No Binance trading key, live order, public hosting or paid runtime service.
- Default bindings are loopback-only.
- New cash cost target: `0 VNĐ`.

See [PRD](docs/PRD.md), [plan](plan.md), [hardware budget](docs/HARDWARE.md) and [zero-cost policy](docs/ZERO_COST.md).

## Repository layout

```text
apps/web/              React + Vite + TypeScript frontend
configs/               Versioned local runtime profiles
data/                  Ignored runtime/research data with tracked manifests only
docs/                  PRD, decisions and operating documentation
models/                Ignored model artifacts with tracked directory markers
reports/               Test/research evidence
scripts/               Windows PowerShell setup/quality/run scripts
src/ntnbinance/         Python backend package
tests/                  Python tests
var/                    Ignored local runtime state/uploads/databases
```

## Prerequisites

- Windows 11 or compatible Windows environment.
- Python 3.14.x for the Stage C lock.
- Node.js 24.x and npm 11.x.
- Git.

Do not use global Python packages for project execution. Docker is not required.

## First-time setup

From PowerShell in the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup.ps1
```

The script creates `.venv`, installs pinned Python dependencies and installs frontend dependencies from `package-lock.json`.

## Quality gate

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\quality.ps1
```

This runs Ruff lint/format check, strict mypy, pytest with coverage threshold, ESLint, Prettier check, TypeScript check, Vitest and frontend production build.

## Smoke test

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\smoke.ps1
```

Expected final output:

```text
backend-smoke: PASS
frontend-smoke: PASS
stage-c-smoke: PASS
```

## Run locally

Terminal 1:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-api.ps1
```

Terminal 2:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-web.ps1
```

Open `http://127.0.0.1:5173`. API development docs are at `http://127.0.0.1:8000/docs` only in `local-dev`.

## Profiles

| Profile | API | Debug/docs | Runtime root | Intended use |
|---|---|---:|---|---|
| `local-dev` | `127.0.0.1:8000` | On | `var/dev` | Development |
| `local-test` | `127.0.0.1:8010` | Off | `var/test` | Automated tests |
| `local-release` | `127.0.0.1:8000` | Off | `var/release` | Private local release |

Select a profile for the API:

```powershell
$env:NTN_PROFILE = "local-release"
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start-api.ps1
```

Profiles reject non-loopback hosts. Public exposure is outside the MVP.

## Dependency updates

Dependency versions are exact-pinned in `pyproject.toml`, `requirements.lock` and `apps/web/package-lock.json`. Before changing them:

1. Review license and advisories.
2. Update [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).
3. Regenerate locks in the project environment.
4. Run the full quality and clean-checkout smoke gates.
5. Record material changes in `docs/decisions/`.

## Data and secrets

- `.env`, private data, uploads, databases, Parquet and model artifacts are ignored.
- Never commit Binance secrets. MVP public market data does not require a trading key.
- Keep runtime data outside the web root.
- Commit only directory markers/manifests explicitly intended for version control.

## Current project stage

See the A–Z tracker at the top of [plan.md](plan.md). Product functionality is intentionally incomplete until its stage gate passes.
