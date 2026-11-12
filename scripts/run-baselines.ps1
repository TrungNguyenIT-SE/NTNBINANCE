$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$CleanRoot = "data\clean\candles\schema_version=1.0.0\run_id=13f11d10018f9914"
$Labels = "data\labels\label_version=1.0.0\run_id=8780c5a42857c830\labels.jsonl"

if (-not (Test-Path $CleanRoot) -or -not (Test-Path $Labels)) {
    throw "Locked Stage F/G runtime data is missing; reproduce those stages first"
}

& ".venv\Scripts\python.exe" -m ntnbinance.baselines.cli `
    --project-root $ProjectRoot `
    --clean-root $CleanRoot `
    --labels $Labels
if ($LASTEXITCODE -ne 0) { throw "Stage I baseline run failed" }
