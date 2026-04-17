#!/bin/bash
cd "$(dirname "$0")"

echo "===================================="
echo "  PDF 比對系統 - Mac 一鍵停止"
echo "===================================="

if ! command -v docker &> /dev/null; then
  echo "找不到 Docker。"
  echo "請按任一鍵結束..."
  read -n 1
  exit 1
fi

if ! docker info > /dev/null 2>&1; then
  echo "Docker 尚未啟動，無法執行停止。"
  echo "請按任一鍵結束..."
  read -n 1
  exit 1
fi

docker compose down

if [ $? -ne 0 ]; then
  echo ""
  echo "停止失敗，請檢查上方訊息。"
  echo "請按任一鍵結束..."
  read -n 1
  exit 1
fi

echo ""
echo "已停止服務。"
echo ""

# Keep terminal open momentarily for user to read output
sleep 2
