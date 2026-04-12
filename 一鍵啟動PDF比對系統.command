#!/bin/zsh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

echo "===================================="
echo "  PDF 比對系統 - 一鍵啟動"
echo "===================================="

if ! command -v docker >/dev/null 2>&1; then
  echo "找不到 Docker，請先安裝 Docker Desktop。"
  echo ""
  read -k 1 "?按任意鍵關閉..."
  echo ""
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker 尚未啟動，請先開啟 Docker Desktop。"
  echo ""
  read -k 1 "?按任意鍵關閉..."
  echo ""
  exit 1
fi

echo "啟動中，第一次可能需要幾分鐘下載模型..."
if docker compose up --build -d; then
  echo ""
  echo "等待服務完成初始化..."
  ready=0
  has_curl=0
  if command -v curl >/dev/null 2>&1; then
    has_curl=1
    for attempt in {1..30}; do
      if curl -fsS "http://localhost:8000/health" >/dev/null 2>&1; then
        ready=1
        break
      fi
      sleep 2
    done
  fi

  echo ""
  if [[ "$ready" == "1" || "$has_curl" == "0" ]]; then
    echo "啟動成功。"
  else
    echo "容器已啟動，系統仍在初始化。"
    echo "若畫面尚未出現，請稍後手動開啟。"
  fi
  echo "前端介面: http://localhost:8000"
  echo "API: http://localhost:8000/api"

  if [[ "$ready" == "1" ]] && command -v open >/dev/null 2>&1; then
    open "http://localhost:8000" >/dev/null 2>&1
  fi
else
  echo ""
  echo "啟動失敗，請檢查上方訊息。"
fi

echo ""
read -k 1 "?按任意鍵關閉..."
echo ""
