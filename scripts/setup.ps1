$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
    python -m venv .venv
}

& ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.lock
if ($LASTEXITCODE -ne 0) { throw "Python lock installation failed" }
& ".venv\Scripts\python.exe" -m pip install --disable-pip-version-check --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw "Local package installation failed" }

Push-Location "apps\web"
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency installation failed" }
    npm prune --ignore-scripts --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency pruning failed" }
}
finally {
    Pop-Location
}

Write-Output "Setup complete. Run: powershell -File scripts\quality.ps1"
