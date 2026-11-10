param(
    [ValidateRange(1, 1440)]
    [int]$Minutes = 2,
    [ValidateSet("1m", "5m", "15m", "1h")]
    [string]$Interval = "1m",
    [string]$DataRoot = "data/raw"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& ".venv\Scripts\python.exe" -m ntnbinance.ingestion.cli stream `
    --minutes $Minutes `
    --interval $Interval `
    --data-root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "Binance public WebSocket capture failed" }
