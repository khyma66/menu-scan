#!/bin/bash

# Comprehensive Workflow Test Script for Menu OCR
# Tests all components end-to-end

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        🧪 Menu OCR - Complete Workflow Test                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_step() {
    echo -n "Testing: $1 ... "
    if eval "$2" > /tmp/test_output.log 2>&1; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        cat /tmp/test_output.log | tail -3
        ((FAILED++))
        return 1
    fi
}

echo "📦 Backend Tests"
echo "─────────────────────────────────────────────────────────────"

# Test 1: Backend imports
test_step "Backend imports" "cd fastapi-menu-service && source venv/bin/activate && python -c 'from app.main import app; print(\"OK\")'"

# Test 2: Run pytest
test_step "Unit tests" "cd fastapi-menu-service && source venv/bin/activate && pytest tests/ -v --tb=short"

# Test 3: Check server startup
echo -n "Testing: Server startup ... "
cd fastapi-menu-service
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/server_test.log 2>&1 &
SERVER_PID=$!
sleep 3
if curl -s http://localhost:8001/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASSED${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAILED${NC}"
    ((FAILED++))
fi
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null
cd ..

echo ""
echo "🎨 Frontend Tests"
echo "─────────────────────────────────────────────────────────────"

# Test 4: Frontend build
test_step "Frontend build" "cd menu-ocr-frontend && npm run build"

# Test 5: TypeScript check
test_step "TypeScript validation" "cd menu-ocr-frontend && npx tsc --noEmit"

echo ""
echo "🔌 API Endpoint Tests"
echo "─────────────────────────────────────────────────────────────"

# Start server for API tests
cd fastapi-menu-service
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8002 > /tmp/api_test.log 2>&1 &
API_PID=$!
sleep 3
cd ..

# Test 6: Root endpoint
test_step "Root endpoint" "curl -s http://localhost:8002/ | grep -q 'Menu OCR API'"

# Test 7: Health endpoint
test_step "Health endpoint" "curl -s http://localhost:8002/health | grep -q 'status'"

# Test 8: API docs
test_step "API documentation" "curl -s http://localhost:8002/docs | grep -q 'swagger'"

# Test 9: OpenAPI schema
test_step "OpenAPI schema" "curl -s http://localhost:8002/openapi.json | grep -q 'openapi'"

# Cleanup
kill $API_PID 2>/dev/null
wait $API_PID 2>/dev/null

echo ""
echo "📁 File Structure Tests"
echo "─────────────────────────────────────────────────────────────"

# Test 10: Required files exist
test_step "Backend files exist" "test -f fastapi-menu-service/app/main.py && test -f fastapi-menu-service/requirements.txt"

test_step "Frontend files exist" "test -f menu-ocr-frontend/app/page.tsx && test -f menu-ocr-frontend/package.json"

test_step "Database schema exists" "test -f fastapi-menu-service/supabase_schema.sql"

test_step "Documentation exists" "test -f DEPLOYMENT.md && test -f AUTH_SETUP.md"

echo ""
echo "📊 Test Summary"
echo "─────────────────────────────────────────────────────────────"
echo -e "✅ Passed: ${GREEN}$PASSED${NC}"
echo -e "❌ Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           ✅ ALL TESTS PASSED! 🎉                           ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║           ❌ SOME TESTS FAILED                               ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
    exit 1
fi

