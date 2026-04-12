#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "===================================="
echo "  PDF 比對系統 - 一鍵停止"
echo "===================================="

if ! command -v docker >/dev/null 2>&1; then
  echo "找不到 Docker。"
  echo ""
  read -k 1 "?按任意鍵關閉..."
  echo ""
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker 尚未啟動，無法執行停止。"
  echo ""
  read -k 1 "?按任意鍵關閉..."
  echo ""
  exit 1
fi

if docker compose down; then
  echo ""
  echo "已停止服務。"
else
  echo ""
  echo "停止失敗，請檢查上方訊息。"
fi

echo ""
read -k 1 "?按任意鍵關閉..."
echo ""
