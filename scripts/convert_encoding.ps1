# Convert UTF-8 .txt files to UTF-8 with BOM .bat files
# This ensures cmd.exe properly reads Chinese characters with chcp 65001

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir

$utf8NoBom = New-Object System.Text.UTF8Encoding $false
$utf8WithBom = New-Object System.Text.UTF8Encoding $true

# Read source files as UTF-8
$startSrc = Join-Path $scriptDir "start_content.txt"
$stopSrc = Join-Path $scriptDir "stop_content.txt"

$startContent = [System.IO.File]::ReadAllText($startSrc, $utf8NoBom)
$stopContent = [System.IO.File]::ReadAllText($stopSrc, $utf8NoBom)

# Find existing .bat files and overwrite them
$startBat = Get-ChildItem -Path $projectDir -Filter "*啟動*.bat" | Select-Object -First 1
$stopBat = Get-ChildItem -Path $projectDir -Filter "*停止*.bat" | Select-Object -First 1

if ($startBat) {
    [System.IO.File]::WriteAllText($startBat.FullName, $startContent, $utf8WithBom)
    Write-Host "OK: Re-encoded $($startBat.Name) as UTF-8 with BOM"
} else {
    $targetPath = Join-Path $projectDir "start_pdf_system.bat"
    [System.IO.File]::WriteAllText($targetPath, $startContent, $utf8WithBom)
    Write-Host "OK: Created $targetPath as UTF-8 with BOM (could not find original Chinese-named file)"
}

if ($stopBat) {
    [System.IO.File]::WriteAllText($stopBat.FullName, $stopContent, $utf8WithBom)
    Write-Host "OK: Re-encoded $($stopBat.Name) as UTF-8 with BOM"
} else {
    $targetPath = Join-Path $projectDir "stop_pdf_system.bat"
    [System.IO.File]::WriteAllText($targetPath, $stopContent, $utf8WithBom)
    Write-Host "OK: Created $targetPath as UTF-8 with BOM (could not find original Chinese-named file)"
}
