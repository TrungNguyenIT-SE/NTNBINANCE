$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$CleanRoot = "data\clean\candles\schema_version=1.0.0\run_id=13f11d10018f9914"
$RawRoot = "data\raw"

if (-not (Test-Path $CleanRoot) -or -not (Test-Path "$RawRoot\manifest.jsonl")) {
    throw "Locked Stage E/F runtime data is missing; reproduce those stages first"
}

& ".venv\Scripts\python.exe" -m ntnbinance.backtest.cli `
    --project-root $ProjectRoot `
    --clean-root $CleanRoot `
    --raw-root $RawRoot
if ($LASTEXITCODE -ne 0) { throw "Stage J backtest failed" }
