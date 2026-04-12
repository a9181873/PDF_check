#!/usr/bin/env bash
set -euo pipefail

# End-to-end test script for PDF diff system
# Prerequisites: Backend server running on http://localhost:8000

OLD_PDF="samples/台灣人壽臻鑽旺旺變額萬能壽險.pdf"
NEW_PDF="samples/台灣人壽金利樂利率變动型養老保險.pdf"

echo "Starting end-to-end tests..."

# Upload PDFs for comparison
RESPONSE=$(curl -s -F "old_pdf=@${OLD_PDF}" -F "new_pdf=@${NEW_PDF}" http://localhost:8000/api/compare/upload)
TASK_ID=$(echo "$RESPONSE" | sed -n -e 's/.*"task_id":\s*"\([^" ]*\)".*/\1/p')

if [ -z "${TASK_ID:-}" ]; then
  echo "Failed to obtain task_id from response: $RESPONSE"
  exit 1
fi

echo "Task ID: ${TASK_ID}"

# Poll status until done or error
while true; do
  STATUS=$(curl -s http://localhost:8000/api/compare/${TASK_ID}/status)
  echo "Status: ${STATUS}"
  if echo "$STATUS" | grep -q '"status":\s*"done"'; then
    break
  fi
  if echo "$STATUS" | grep -q '"status":\s*"error"'; then
    echo "Task reported error. Exiting."
    exit 1
  fi
  sleep 2
done

# Retrieve result (diff report)
echo "Fetching diff report..."
curl -s http://localhost:8000/api/compare/${TASK_ID}/result | head -n 50

# Download old/new PDFs for verification
echo "Downloading old/new PDFs..."
curl -s http://localhost:8000/api/compare/${TASK_ID}/pdf/old -o "samples/${TASK_ID}_old.pdf"
curl -s http://localhost:8000/api/compare/${TASK_ID}/pdf/new -o "samples/${TASK_ID}_new.pdf"

# Download markdown manifests
echo "Downloading markdown manifests..."
curl -s http://localhost:8000/api/compare/${TASK_ID}/markdown -o "markdown_${TASK_ID}.json" 
curl -s http://localhost:8000/api/compare/${TASK_ID}/markdown/old -o "markdown_${TASK_ID}_old.md" 
curl -s http://localhost:8000/api/compare/${TASK_ID}/markdown/new -o "markdown_${TASK_ID}_new.md" 

echo "End-to-end test completed."
