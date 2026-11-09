$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$env:NTN_PROFILE = "local-test"
& ".venv\Scripts\python.exe" -c "from fastapi.testclient import TestClient; from ntnbinance.main import create_app; c=TestClient(create_app()); assert c.get('/health/live').json()=={'status':'ok'}; assert c.get('/api/v1/meta').json()['trading_enabled'] is False; print('backend-smoke: PASS')"
if ($LASTEXITCODE -ne 0) { throw "Backend smoke test failed" }

Push-Location "apps\web"
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
    if (-not (Test-Path "dist\index.html")) {
        throw "Frontend build did not create dist/index.html"
    }
    Write-Output "frontend-smoke: PASS"
}
finally {
    Pop-Location
}

Write-Output "stage-c-smoke: PASS"
