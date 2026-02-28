#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${API_PORT:-8000}"
API_LOCAL_URL="http://localhost:${API_PORT}"
TEST_IMAGE="${TEST_IMAGE:-$ROOT_DIR/tests/assets/test_menu_clear.png}"
BACKEND_LOG="/tmp/menu_ocr_backend.log"
CLOUDFLARED_LOG="/tmp/menu_ocr_cloudflared.log"
BACKEND_STARTED_BY_SCRIPT=0
BACKEND_PID=""
CLOUDFLARED_PID=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

pass() {
  echo -e "${GREEN}✅ $1${NC}"
  PASSED=$((PASSED + 1))
}

fail() {
  echo -e "${RED}❌ $1${NC}"
  FAILED=$((FAILED + 1))
}

cleanup() {
  if [[ -n "$CLOUDFLARED_PID" ]] && kill -0 "$CLOUDFLARED_PID" >/dev/null 2>&1; then
    kill "$CLOUDFLARED_PID" >/dev/null 2>&1 || true
    wait "$CLOUDFLARED_PID" 2>/dev/null || true
  fi

  if [[ "$BACKEND_STARTED_BY_SCRIPT" -eq 1 ]] && [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

echo "============================================================"
echo "Menu OCR E2E: localhost + Cloudflare tunnel"
echo "============================================================"

if [[ ! -f "$TEST_IMAGE" ]]; then
  echo -e "${RED}Test image not found: $TEST_IMAGE${NC}"
  exit 1
fi

ensure_backend_running() {
  if curl -fsS "$API_LOCAL_URL/health" >/dev/null 2>&1; then
    echo -e "${YELLOW}Using existing local FastAPI at $API_LOCAL_URL${NC}"
    return
  fi

  echo -e "${YELLOW}Starting local FastAPI for test mode...${NC}"
  cd "$ROOT_DIR/fastapi-menu-service"

  if [[ ! -f "venv/bin/activate" ]]; then
    echo -e "${RED}Missing virtual environment: fastapi-menu-service/venv${NC}"
    echo "Create it first: cd fastapi-menu-service && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
  fi

  set +u
  source venv/bin/activate
  set -u
  uvicorn app.main:app --host 0.0.0.0 --port "$API_PORT" >"$BACKEND_LOG" 2>&1 &
  BACKEND_PID=$!
  BACKEND_STARTED_BY_SCRIPT=1

  for _ in {1..20}; do
    if curl -fsS "$API_LOCAL_URL/health" >/dev/null 2>&1; then
      echo -e "${GREEN}Local FastAPI started on $API_LOCAL_URL${NC}"
      cd "$ROOT_DIR"
      return
    fi
    sleep 1
  done

  echo -e "${RED}FastAPI failed to start. Last backend logs:${NC}"
  tail -n 40 "$BACKEND_LOG" || true
  exit 1
}

test_api_base() {
  local base_url="$1"
  local label="$2"

  echo ""
  echo "--- Testing $label ($base_url) ---"

  if [[ "$label" == "cloudflare" ]]; then
    for _ in {1..20}; do
      if curl -fsS "$base_url/health" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
  fi

  if curl -fsS "$base_url/health" | grep -q '"status"'; then
    pass "$label health endpoint"
  else
    fail "$label health endpoint"
  fi

  if curl -fsS "$base_url/" | grep -q 'Menu OCR API'; then
    pass "$label root endpoint"
  else
    fail "$label root endpoint"
  fi

  local http_code
  http_code=$(curl -s -o /tmp/menu_ocr_ocr_response.json -w "%{http_code}" \
    -X POST "$base_url/ocr/process-upload" \
    -F "image=@${TEST_IMAGE}" \
    -F "use_llm_enhancement=false" \
    -F "language=auto" \
    -F "output_language=en")

  if [[ "$http_code" == "200" ]] && grep -q '"success":true' /tmp/menu_ocr_ocr_response.json; then
    pass "$label OCR process-upload endpoint"
  else
    fail "$label OCR process-upload endpoint (HTTP $http_code)"
    tail -n 20 /tmp/menu_ocr_ocr_response.json || true
  fi
}

start_cloudflare_tunnel() {
  if ! command -v cloudflared >/dev/null 2>&1; then
    echo -e "${YELLOW}cloudflared is not installed. Skipping Cloudflare dev-mode test.${NC}"
    return 1
  fi

  : >"$CLOUDFLARED_LOG"
  cloudflared tunnel --url "$API_LOCAL_URL" --no-autoupdate >"$CLOUDFLARED_LOG" 2>&1 &
  CLOUDFLARED_PID=$!

  for _ in {1..30}; do
    local tunnel_url
    tunnel_url=$(grep -aEo 'https://[-a-zA-Z0-9]+\.trycloudflare\.com' "$CLOUDFLARED_LOG" | head -n1 | tr -d '\r\n' || true)
    if [[ -n "$tunnel_url" ]]; then
      echo "$tunnel_url"
      return 0
    fi
    sleep 1
  done

  echo -e "${RED}Cloudflare tunnel URL not detected. Logs:${NC}"
  tail -n 40 "$CLOUDFLARED_LOG" || true
  return 1
}

ensure_backend_running
cd "$ROOT_DIR"

test_api_base "$API_LOCAL_URL" "localhost"

TUNNEL_URL=""
if TUNNEL_URL=$(start_cloudflare_tunnel); then
  echo -e "${GREEN}Cloudflare tunnel ready: $TUNNEL_URL${NC}"
  test_api_base "$TUNNEL_URL" "cloudflare"
  echo ""
  echo "Cloudflare dev endpoint (temporary): $TUNNEL_URL"
else
  fail "cloudflare tunnel setup"
fi

echo ""
echo "============================================================"
echo -e "Passed: ${GREEN}${PASSED}${NC}"
echo -e "Failed: ${RED}${FAILED}${NC}"
echo "============================================================"

if [[ "$FAILED" -gt 0 ]]; then
  exit 1
fi
