$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $ProjectRoot "apps\web")
try {
    npm run dev
    if ($LASTEXITCODE -ne 0) { throw "Frontend process exited with an error" }
}
finally {
    Pop-Location
}
