# Create startup and stop .bat files with UTF-8 BOM encoding
$projectRoot = Split-Path -Parent $PSScriptRoot

$startContent = Get-Content -Path "$PSScriptRoot\start_content.txt" -Raw
$stopContent  = Get-Content -Path "$PSScriptRoot\stop_content.txt" -Raw

$utf8BOM = New-Object System.Text.UTF8Encoding($true)

$startPath = Join-Path $projectRoot ([char]0x4E00 + [char]0x9375 + [char]0x555F + [char]0x52D5 + "PDF" + [char]0x6BD4 + [char]0x5C0D + [char]0x7CFB + [char]0x7D71 + ".bat")
$stopPath  = Join-Path $projectRoot ([char]0x4E00 + [char]0x9375 + [char]0x505C + [char]0x6B62 + "PDF" + [char]0x6BD4 + [char]0x5C0D + [char]0x7CFB + [char]0x7D71 + ".bat")

[System.IO.File]::WriteAllText($startPath, $startContent, $utf8BOM)
[System.IO.File]::WriteAllText($stopPath,  $stopContent,  $utf8BOM)

Write-Host "Created: $startPath"
Write-Host "Created: $stopPath"
