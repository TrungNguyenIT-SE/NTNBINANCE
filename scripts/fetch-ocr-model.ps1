$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$TargetRoot = Join-Path $ProjectRoot "models\ocr"
$Commit = "87416418657359cb625c412a48b6e1d6d41c29bd"
$ModelHash = "7D4322BD2A7749724879683FC3912CB542F19906C83BCC1A52132556427170B2"
$LicenseHash = "CFC7749B96F63BD31C3C42B5C471BF756814053E847C10F3EB003417BC523D30"

New-Item -ItemType Directory -Path $TargetRoot -Force | Out-Null

function Get-VerifiedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$ExpectedHash,
        [string]$TargetName = $Name
    )
    $Target = Join-Path $TargetRoot $TargetName
    if ((Test-Path -LiteralPath $Target) -and
        ((Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash -eq $ExpectedHash)) {
        return
    }
    $Temporary = "$Target.download"
    $Uri = "https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/$Commit/$Name"
    Invoke-WebRequest -UseBasicParsing -Uri $Uri -OutFile $Temporary
    $ActualHash = (Get-FileHash -LiteralPath $Temporary -Algorithm SHA256).Hash
    if ($ActualHash -ne $ExpectedHash) {
        Remove-Item -LiteralPath $Temporary -Force
        throw "OCR asset checksum mismatch for $Name"
    }
    Move-Item -LiteralPath $Temporary -Destination $Target -Force
}

Get-VerifiedFile -Name "eng.traineddata" -ExpectedHash $ModelHash
Get-VerifiedFile -Name "LICENSE" -ExpectedHash $LicenseHash -TargetName "LICENSE.tessdata-fast"

Write-Output "OCR model and license verified at tessdata_fast commit $Commit"
