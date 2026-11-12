$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\ntnbinance-labels.exe" @args
if ($LASTEXITCODE -ne 0) { throw "Stage G label generation failed" }
