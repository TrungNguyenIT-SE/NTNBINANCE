$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\ntnbinance-split.exe" @args
if ($LASTEXITCODE -ne 0) { throw "Stage H split lock failed" }
