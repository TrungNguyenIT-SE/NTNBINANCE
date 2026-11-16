$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\python.exe" "scripts\run-model-selection.py"
if ($LASTEXITCODE -ne 0) { throw "Stage O model selection failed" }
