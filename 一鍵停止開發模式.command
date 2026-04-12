#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "===================================="
echo "  PDF 比對系統 - 停止開發模式"
echo "===================================="

PID_FILE="$SCRIPT_DIR/.dev-pids"
killed=0

# Kill processes from PID file
if [ -f "$PID_FILE" ]; then
  while IFS= read -r pid; do
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null
      killed=$((killed + 1))
      echo "已停止進程 PID $pid"
    fi
  done < "$PID_FILE"
  rm -f "$PID_FILE"
fi

# Also kill any remaining uvicorn / vite on known ports
for port in 8000 5173; do
  pids=$(lsof -ti ":$port" 2>/dev/null)
  if [ -n "$pids" ]; then
    echo "$pids" | xargs kill 2>/dev/null
    killed=$((killed + 1))
    echo "已釋放 port $port"
  fi
done

echo ""
if [ "$killed" -gt 0 ]; then
  echo "開發模式已停止。"
else
  echo "未發現運行中的開發服務。"
fi

echo ""
read -k 1 "?按任意鍵關閉..."
echo ""
