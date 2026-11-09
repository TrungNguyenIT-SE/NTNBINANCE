$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not $env:NTN_PROFILE) {
    $env:NTN_PROFILE = "local-dev"
}

& ".venv\Scripts\python.exe" -m ntnbinance.main
if ($LASTEXITCODE -ne 0) { throw "API process exited with an error" }
