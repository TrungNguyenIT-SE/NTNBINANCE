param(
    [string]$DataRoot = "data/raw"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\python.exe" -m ntnbinance.ingestion.cli audit --data-root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "Raw ingestion manifest audit failed" }
