#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MCP_HOST="127.0.0.1"
MCP_PORT="${MCP_PORT:-8001}"
MCP_URL="http://${MCP_HOST}:${MCP_PORT}"
API_BASE="${MENU_OCR_API_BASE:-http://127.0.0.1:8787}"
TOKEN="${SMOKE_TEST_BEARER_TOKEN:-}"
MCP_VENV="${ROOT_DIR}/.venv-smoke-mcp"
API_WORKER_DIR="${ROOT_DIR}/menu-ocr-app/workers/api-worker"
API_VENV="${API_WORKER_DIR}/.venv-smoke-api"
START_API_WORKER="${START_API_WORKER:-1}"

MCP_PID=""
API_PID=""

cleanup() {
  if [[ -n "${API_PID}" ]] && kill -0 "${API_PID}" 2>/dev/null; then
    kill "${API_PID}" >/dev/null 2>&1 || true
    wait "${API_PID}" 2>/dev/null || true
  fi
  if [[ -n "${MCP_PID}" ]] && kill -0 "${MCP_PID}" 2>/dev/null; then
    kill "${MCP_PID}" >/dev/null 2>&1 || true
    wait "${MCP_PID}" 2>/dev/null || true
  fi
}
trap cleanup EXIT

echo "=== Menu OCR v3 + MCP Smoke Test ==="
echo "API_BASE=${API_BASE}"
echo "MCP_URL=${MCP_URL}"

if [[ "${START_API_WORKER}" == "1" ]]; then
  echo "[0/6] Starting local v3 API worker..."
  ENV_FILE=""
  if [[ -f "${API_WORKER_DIR}/.dev.vars" ]]; then
    ENV_FILE="${API_WORKER_DIR}/.dev.vars"
  elif [[ -f "${API_WORKER_DIR}/.env" ]]; then
    ENV_FILE="${API_WORKER_DIR}/.env"
  else
    echo "❌ Missing ${API_WORKER_DIR}/.dev.vars and ${API_WORKER_DIR}/.env"
    exit 1
  fi
  if [[ ! -d "${API_VENV}" ]]; then
    python3 -m venv "${API_VENV}"
  fi
  "${API_VENV}/bin/python" -m pip install --quiet --upgrade pip
  "${API_VENV}/bin/pip" install --quiet -r "${API_WORKER_DIR}/requirements.txt"
  (
    cd "${API_WORKER_DIR}/src"
    set -a
    source "${ENV_FILE}"
    set +a
    exec ../.venv-smoke-api/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8787
  ) >/tmp/menu_ocr_api_worker.log 2>&1 &
  API_PID=$!

  for _ in {1..30}; do
    if curl -fsS "${API_BASE}/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done
fi

echo "[0/6] Preparing Python runtime for MCP bridge..."
if [[ ! -d "${MCP_VENV}" ]]; then
  python3 -m venv "${MCP_VENV}"
fi
"${MCP_VENV}/bin/python" -m pip install --quiet --upgrade pip
"${MCP_VENV}/bin/pip" install --quiet fastapi uvicorn httpx

echo "[1/6] Starting MCP bridge server..."
"${MCP_VENV}/bin/python" "${ROOT_DIR}/scripts/android_mcp_server.py" >/tmp/android_mcp_server.log 2>&1 &
MCP_PID=$!

for _ in {1..20}; do
  if curl -fsS "${MCP_URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

if ! curl -fsS "${MCP_URL}/health" >/dev/null 2>&1; then
  echo "❌ MCP server did not start. Logs: /tmp/android_mcp_server.log"
  exit 1
fi
echo "✅ MCP bridge is healthy"

echo "[2/6] Checking backend health endpoint..."
if curl -fsS "${API_BASE}/health" >/dev/null 2>&1; then
  echo "✅ Backend /health reachable"
else
  echo "❌ Backend /health unreachable at ${API_BASE}"
  echo "   Start your API worker locally (example: wrangler dev) and re-run."
  exit 1
fi

echo "[3/6] Checking /test-db write endpoint..."
TEST_DB_ARGS=("-s" "-o" "/tmp/smoke_test_db_resp.json" "-w" "%{http_code}" "${API_BASE}/test-db")
if [[ -n "${TOKEN}" ]]; then
  TEST_DB_ARGS=("-H" "Authorization: Bearer ${TOKEN}" "${TEST_DB_ARGS[@]}")
fi
TEST_DB_STATUS=$(curl "${TEST_DB_ARGS[@]}")
if [[ "${TEST_DB_STATUS}" == "200" ]]; then
  echo "✅ /test-db succeeded"
else
  echo "❌ /test-db failed (${TEST_DB_STATUS})"
  cat /tmp/smoke_test_db_resp.json || true
  exit 1
fi

echo "[4/6] Checking protected health-profile endpoint behavior..."
PROFILE_STATUS=$(curl -s -o /tmp/smoke_profile_resp.json -w "%{http_code}" "${API_BASE}/v1/user/health-profile")
if [[ "${PROFILE_STATUS}" == "401" || "${PROFILE_STATUS}" == "403" ]]; then
  echo "✅ /v1/user/health-profile is auth-protected (${PROFILE_STATUS})"
elif [[ "${PROFILE_STATUS}" == "200" ]]; then
  echo "✅ /v1/user/health-profile returned 200 without token (dev mode)"
else
  echo "❌ Unexpected status for /v1/user/health-profile: ${PROFILE_STATUS}"
  cat /tmp/smoke_profile_resp.json || true
  exit 1
fi

echo "[5/6] Checking MCP bridge health call path..."
if curl -fsS "${MCP_URL}/health" >/dev/null 2>&1; then
  echo "✅ MCP /health reachable"
else
  echo "❌ MCP /health not reachable"
  exit 1
fi

echo "[6/6] Calling MCP method get_health_profile..."
if [[ -n "${TOKEN}" ]]; then
  MCP_BODY=$(cat <<EOF
{"method":"get_health_profile","token":"${TOKEN}"}
EOF
)
  MCP_STATUS=$(curl -s -o /tmp/smoke_mcp_resp.json -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -d "${MCP_BODY}" \
    "${MCP_URL}/mcp/call")

  if [[ "${MCP_STATUS}" == "200" ]]; then
    echo "✅ MCP get_health_profile succeeded with token"
  else
    echo "❌ MCP get_health_profile failed (${MCP_STATUS})"
    cat /tmp/smoke_mcp_resp.json || true
    exit 1
  fi
else
  echo "⚠️ SMOKE_TEST_BEARER_TOKEN not set; verifying expected auth failure path"
  MCP_BODY='{"method":"get_health_profile","token":""}'
  MCP_STATUS=$(curl -s -o /tmp/smoke_mcp_resp.json -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -d "${MCP_BODY}" \
    "${MCP_URL}/mcp/call")

  if [[ "${MCP_STATUS}" == "401" || "${MCP_STATUS}" == "403" || "${MCP_STATUS}" == "500" ]]; then
    echo "✅ MCP auth path behaves as expected without token (${MCP_STATUS})"
  else
    echo "❌ Unexpected MCP status without token: ${MCP_STATUS}"
    cat /tmp/smoke_mcp_resp.json || true
    exit 1
  fi
fi

echo "[7/7] Smoke test completed"
echo "✅ PASS: MCP bridge + /health + /test-db + profile endpoint checks completed"
