# Docker Quickstart

## 0) One-Click 啟動（給不想打指令的人）

在專案根目錄直接雙擊：

- macOS：
  - `一鍵啟動PDF比對系統.command`
  - `一鍵停止PDF比對系統.command`
- Windows：
  - `一鍵啟動PDF比對系統.bat`
  - `一鍵停止PDF比對系統.bat`

## 1) First run on this computer

```bash
cd /path/to/PDF_check
docker compose up --build -d
```

- API URL: `http://localhost:8000`
- Health check: `http://localhost:8000/health`

Stop service:

```bash
docker compose down
```

## 2) Move to another computer (portable image)

After build completes on source computer:

```bash
cd /path/to/PDF_check
docker save -o pdf-check-backend.tar pdf-check-backend:latest
```

Copy `pdf-check-backend.tar` to the new computer, then:

```bash
docker load -i pdf-check-backend.tar
cd /path/to/PDF_check
docker compose up -d
```

## 3) Data persistence

The compose file stores runtime data in Docker volumes:

- `backend_runtime`: SQLite DB, uploads, exports
- `backend_hf_cache`: Docling/HuggingFace model cache

This means restarting containers will not lose app data.

Default OCR languages in Docker: `eng,chi_tra` (via `OCR_LANGS`).

## 4) Recommended hardware

This project is primarily `CPU + RAM` bound (Docling parse + OCR + diff flow). GPU is optional.

- Minimum usable: `4 CPU cores / 8GB RAM / SSD`
- Recommended: `8+ CPU cores / 16GB RAM / SSD`
- Team usage / multiple concurrent jobs: `12+ CPU cores / 32GB RAM / SSD`

From local benchmark samples (`10-core CPU / 24GB RAM`):

- 4-8 page PDFs: around `25-31 sec` per file
- Peak memory: around `2.2-2.9 GB`

## 5) Notes

- First Docling run may be slower because model files initialize.
- If `docker compose` shows daemon errors, start Docker Desktop first.
- Each comparison now auto-saves parsed markdown files to:
  - `backend/exports/markdown/<task_id>_old.md`
  - `backend/exports/markdown/<task_id>_new.md`
