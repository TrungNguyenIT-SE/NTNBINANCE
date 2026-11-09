$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location (Join-Path $ProjectRoot "apps\web")
try {
    npm ls --depth=0
    if ($LASTEXITCODE -ne 0) { throw "Frontend dependency tree is inconsistent" }
    npm run check
    if ($LASTEXITCODE -ne 0) { throw "Frontend quality gate failed" }
}
finally {
    Pop-Location
}
