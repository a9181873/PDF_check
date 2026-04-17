# PDF Check 系統 - 一鍵打包成離線部署包
#
# 用途：
#   本機建置 Docker 映像 → 匯出 tar → 與 docker-compose.yml 打包成 zip
#   交付後對方只要有 Docker Desktop 即可 `docker load` + `docker compose up -d`
#
# 用法：
#   .\build-and-export.ps1                # 預設版本號 1.0
#   .\build-and-export.ps1 -Version 1.2   # 自訂版本號

param(
    [string]$Version = "1.0",
    [string]$OutDir  = "dist-package"
)

$ErrorActionPreference = "Stop"

$ImageName = "pdf-check-backend"
$TaggedImage = "${ImageName}:${Version}"
$StampedImage = "${ImageName}:latest"

Write-Host ""
Write-Host "=== PDF Check 離線部署包建置 ===" -ForegroundColor Cyan
Write-Host "版本: $Version"
Write-Host "輸出: $OutDir"
Write-Host ""

# 1. 前置檢查
Write-Host "[1/5] 檢查 Docker..." -ForegroundColor Yellow
docker version --format '{{.Server.Version}}' | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker 未執行，請先啟動 Docker Desktop" -ForegroundColor Red
    exit 1
}

# 2. 建置映像
Write-Host "[2/5] 建置映像（需 3-10 分鐘）..." -ForegroundColor Yellow
docker compose build
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: build 失敗" -ForegroundColor Red; exit 1 }

# 3. 打版本 tag
Write-Host "[3/5] 打版本 tag $TaggedImage ..." -ForegroundColor Yellow
docker tag $StampedImage $TaggedImage

# 4. 建輸出目錄 + 匯出 tar
if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
New-Item -ItemType Directory -Path $OutDir | Out-Null

$TarFile = Join-Path $OutDir "${ImageName}_${Version}.tar"
Write-Host "[4/5] 匯出映像 → $TarFile （約 1-2 GB）..." -ForegroundColor Yellow
docker save $TaggedImage -o $TarFile
if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: save 失敗" -ForegroundColor Red; exit 1 }

# 複製 compose 檔（替換版本號）
$ComposeOut = Join-Path $OutDir "docker-compose.yml"
(Get-Content "docker-compose.yml" -Raw) `
    -replace "${ImageName}:latest", $TaggedImage `
    | Set-Content $ComposeOut -Encoding UTF8

# 複製 README 部署說明（若存在）
if (Test-Path "DEPLOY.md") {
    Copy-Item "DEPLOY.md" (Join-Path $OutDir "README.md")
}

# 5. 壓成 zip
Write-Host "[5/5] 壓縮為 zip..." -ForegroundColor Yellow
$ZipFile = "${ImageName}_${Version}.zip"
if (Test-Path $ZipFile) { Remove-Item -Force $ZipFile }
Compress-Archive -Path "$OutDir\*" -DestinationPath $ZipFile -CompressionLevel Optimal

$TarSize = "{0:N0}" -f ((Get-Item $TarFile).Length / 1MB)
$ZipSize = "{0:N0}" -f ((Get-Item $ZipFile).Length / 1MB)

Write-Host ""
Write-Host "=== 完成 ===" -ForegroundColor Green
Write-Host "tar 檔: $TarFile ($TarSize MB)"
Write-Host "zip 檔: $ZipFile ($ZipSize MB)"
Write-Host ""
Write-Host "交付清單（zip 內）：" -ForegroundColor Cyan
Write-Host "  - ${ImageName}_${Version}.tar   （Docker 映像）"
Write-Host "  - docker-compose.yml            （啟動配置）"
Write-Host "  - README.md                     （部署說明）"
Write-Host ""
Write-Host "對方電腦執行：" -ForegroundColor Cyan
Write-Host "  docker load -i ${ImageName}_${Version}.tar"
Write-Host "  docker compose up -d"
Write-Host "  瀏覽器開 http://localhost:8000"
