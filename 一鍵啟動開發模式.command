#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "===================================="
echo "  PDF 比對系統 - 開發模式啟動"
echo "===================================="

# ---------- Python check ----------
if ! command -v python3 >/dev/null 2>&1; then
  echo "找不到 python3，請先安裝 Python 3.10+。"
  echo ""
  read -k 1 "?按任意鍵關閉..."
  echo ""
  exit 1
fi

# ---------- Node / npm check ----------
if ! command -v npm >/dev/null 2>&1; then
  echo "找不到 npm，請先安裝 Node.js 18+。"
  echo ""
  read -k 1 "?按任意鍵關閉..."
  echo ""
  exit 1
fi

# ---------- Backend venv ----------
VENV_DIR="$SCRIPT_DIR/backend/.venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "建立 Python 虛擬環境..."
  python3 -m venv "$VENV_DIR"
fi

echo "安裝 backend 依賴..."
"$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/backend/requirements.txt"

# ---------- Frontend deps ----------
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
  echo "安裝 frontend 依賴..."
  (cd "$SCRIPT_DIR/frontend" && npm install --silent)
fi

# ---------- Runtime dirs ----------
mkdir -p "$SCRIPT_DIR/runtime/uploads/old" "$SCRIPT_DIR/runtime/uploads/new" "$SCRIPT_DIR/runtime/exports/markdown"

# ---------- PID file ----------
PID_FILE="$SCRIPT_DIR/.dev-pids"
: > "$PID_FILE"

# ---------- Start backend ----------
echo "啟動 Backend (uvicorn :8000)..."
(
  cd "$SCRIPT_DIR/backend" && \
  "$VENV_DIR/bin/uvicorn" main:app --reload --host 127.0.0.1 --port 8000 \
    2>&1 | while IFS= read -r line; do echo "[backend] $line"; done
) &
BACKEND_PID=$!
echo "$BACKEND_PID" >> "$PID_FILE"

# ---------- Start frontend ----------
echo "啟動 Frontend (vite :5173)..."
(
  cd "$SCRIPT_DIR/frontend" && \
  npm run dev 2>&1 | while IFS= read -r line; do echo "[frontend] $line"; done
) &
FRONTEND_PID=$!
echo "$FRONTEND_PID" >> "$PID_FILE"

# ---------- Wait for backend ready ----------
echo ""
echo "等待服務就緒..."
ready=0
for attempt in {1..20}; do
  if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done

echo ""
if [ "$ready" = "1" ]; then
  echo "啟動成功！"
else
  echo "Backend 仍在初始化，請稍候..."
fi

echo ""
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  API:      http://localhost:8000/api"
echo ""
echo "  停止服務: 雙擊「一鍵停止開發模式.command」"
echo "           或按 Ctrl+C"
echo ""

# Open browser
if [ "$ready" = "1" ] && command -v open >/dev/null 2>&1; then
  open "http://localhost:5173" >/dev/null 2>&1
fi

# ---------- Trap Ctrl+C to clean up ----------
cleanup() {
  echo ""
  echo "正在停止服務..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  rm -f "$PID_FILE"
  echo "已停止。"
}
trap cleanup INT TERM

# Keep script alive
wait
