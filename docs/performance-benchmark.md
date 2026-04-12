# PDF 解析效能量測

## 目的

用同一套腳本在不同硬體（例如 macOS 與 Windows）測量：

- PDF 解析時間（每次 run 的 elapsed seconds）
- 解析過程 CPU 使用率（平均/峰值）
- 解析過程記憶體使用量（平均/峰值 RSS）
- 解析引擎（docling / fallback）

## 量測腳本

- 腳本位置：`backend/scripts/benchmark_parser.py`
- 輸出格式：`JSON + CSV`
- 預設輸出資料夾：`backend/benchmarks/`

## 本機執行 (macOS/Linux)

```bash
cd /path/to/PDF_check/backend
source .venv/bin/activate
python scripts/benchmark_parser.py \
  --pdf ../samples/台灣人壽金利樂利率變動型養老保險.pdf \
  --pdf ../samples/台灣人壽臻鑽旺旺變額萬能壽險.pdf \
  --warmup 1 \
  --repeat 3 \
  --tag macbook
```

## Windows 執行 (PowerShell)

```powershell
cd C:\path\to\PDF_check\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OCR_LANGS = "eng,chi_tra"

python scripts\benchmark_parser.py \
  --pdf ..\samples\台灣人壽金利樂利率變動型養老保險.pdf \
  --pdf ..\samples\台灣人壽臻鑽旺旺變額萬能壽險.pdf \
  --warmup 1 \
  --repeat 3 \
  --tag windows
```

## 報表重點欄位

- `hardware`: 主機硬體與環境快照（CPU 核心數、總記憶體、平台資訊）
- `files[].runs[]`: 每次量測明細
  - `elapsed_sec`
  - `peak_rss_bytes`
  - `avg_cpu_percent` / `peak_cpu_percent`
  - `engine`
- `files[].summary`: 每份 PDF 的聚合結果（平均、最小、最大）

## 建議比較方法

1. macOS 與 Windows 使用相同 `--warmup` / `--repeat`。
2. 先看 `elapsed_sec_avg` 與 `peak_rss_mb_max`。
3. 確認 `engine_set` 都是 `docling`，避免拿 fallback 結果比較。
4. 若 Windows 首次 run 明顯較慢，先排除模型初次下載影響（看 warmup 後的平均值）。
