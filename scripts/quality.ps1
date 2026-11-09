$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\ruff.exe" check .
if ($LASTEXITCODE -ne 0) { throw "Ruff lint failed" }
& ".venv\Scripts\ruff.exe" format --check .
if ($LASTEXITCODE -ne 0) { throw "Ruff format check failed" }
& ".venv\Scripts\mypy.exe"
if ($LASTEXITCODE -ne 0) { throw "Mypy failed" }
& ".venv\Scripts\python.exe" -m pip check
if ($LASTEXITCODE -ne 0) { throw "Python dependency consistency check failed" }
& ".venv\Scripts\pytest.exe"
if ($LASTEXITCODE -ne 0) { throw "Pytest failed" }
& powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\frontend-check.ps1"
if ($LASTEXITCODE -ne 0) { throw "Frontend check script failed" }

Write-Output "All quality gates passed."
