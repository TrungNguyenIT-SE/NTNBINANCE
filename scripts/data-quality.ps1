$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\ntnbinance-quality.exe" @args
if ($LASTEXITCODE -ne 0) { throw "Stage F data-quality pipeline failed" }
