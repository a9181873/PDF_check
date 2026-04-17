# PDF 比對系統 - 部署指南

保險 DM 雙版本 PDF 比對工具（FastAPI 後端 + React 前端）。

---

## 系統需求

- **Windows 10/11、macOS 或 Linux**
- **Docker Desktop**（Windows/Mac 需手動安裝，Linux 可用 `docker` + `docker compose` plugin）
  - Docker 官方下載：<https://www.docker.com/products/docker-desktop/>
  - 安裝完首次啟動後，需等 whale icon 從「Starting」轉為「Running」
- **硬碟空間**：約 4 GB（映像約 1-2 GB，OCR 模型快取 +資料）
- **RAM**：建議 4 GB 以上

---

## 安裝步驟

### 1. 確認 Docker 已啟動
```powershell
docker version
```
要看到 `Server: Docker Desktop` 區塊（非只有 Client）。若未啟動，開啟 Docker Desktop 等待其 ready。

### 2. 載入映像
收到的 zip 解壓後，在該資料夾執行：
```powershell
docker load -i pdf-check-backend_1.0.tar
```
看到 `Loaded image: pdf-check-backend:1.0` 即成功（約 30 秒 - 2 分鐘）。

### 3. 啟動服務
```powershell
docker compose up -d
```
首次啟動約 10-30 秒。檢查是否正常：
```powershell
docker compose ps
docker compose logs -f backend
```
看到 `Uvicorn running on http://0.0.0.0:8000` 即 ready。

### 4. 開啟瀏覽器
<http://localhost:8000>

---

## 日常操作

| 動作 | 指令 |
|---|---|
| 啟動 | `docker compose up -d` |
| 停止 | `docker compose down` |
| 查看 log | `docker compose logs -f backend` |
| 重啟 | `docker compose restart backend` |
| 看容器狀態 | `docker compose ps` |

---

## 資料保存

所有上傳 PDF、比對結果、快照會存在 Docker 命名卷：
- `backend_runtime` — 上傳檔案、比對報告、快照 PNG
- `backend_hf_cache` — OCR 模型快取（首次用會下載）

**資料位置**：Docker 管理，不在本機資料夾。若要備份：
```powershell
docker run --rm -v backend_runtime:/data -v ${PWD}:/backup alpine tar czf /backup/backend_runtime_backup.tgz -C /data .
```

若要**清空全部資料**（謹慎）：
```powershell
docker compose down -v
```

---

## 疑難排解

### 啟動後 http://localhost:8000 連不上
- 檢查 `docker compose ps`，status 應為 `running`
- 8000 port 被佔用：改 `docker-compose.yml` 中 `"8000:8000"` 為 `"8080:8000"`，改用 <http://localhost:8080>

### Windows 下看到「Hardware assisted virtualization」錯誤
BIOS 需開 VT-x/SVM。或改用 WSL2 後端的 Docker Desktop。

### 比對結果全空 / 顯示錯誤
查 log：`docker compose logs backend | tail -100`
最常見：上傳 PDF 檔壞掉、或 PDF 受密碼保護。

### 映像載入失敗 `invalid tar header`
tar 檔下載中斷。重傳一次完整檔案。

---

## 升級到新版

收到新版 zip 後：
```powershell
docker compose down
docker load -i pdf-check-backend_1.1.tar
# 編輯 docker-compose.yml，把 image 版本改為新版
docker compose up -d
```
資料卷不會被刪，過去比對紀錄保留。

---

## 聯絡

有問題回報時請附上：
- `docker compose logs backend | tail -200` 輸出
- 觸發問題的 PDF（若可）
- Docker 版本：`docker version`
