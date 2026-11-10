param(
    [ValidateRange(1, 720)]
    [int]$Hours = 24,
    [string]$DataRoot = "data/raw"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\python.exe" -m ntnbinance.ingestion.cli backfill `
    --hours $Hours `
    --data-root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "Binance public-data backfill failed" }
