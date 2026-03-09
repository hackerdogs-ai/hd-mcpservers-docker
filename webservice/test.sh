#!/bin/bash
# Test script for Tools Web Service API
# Run this after the API is already running (locally or in Docker).
# Usage: ./test.sh [BASE_URL]
# Example: ./test.sh
# Example: ./test.sh http://localhost:8000
# Example: ./test.sh http://localhost:8080

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${1:-http://localhost:8000}"
BASE_URL="${BASE_URL%/}"
PASS=0
FAIL=0

pass() { echo -e "  ${GREEN}✅ PASS: $1${NC}"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}❌ FAIL: $1${NC}"; FAIL=$((FAIL + 1)); }
info() { echo -e "${BLUE}$1${NC}"; }

echo "================================================================================="
echo -e "${BLUE}Tools Web Service — API Test Suite${NC}"
echo "================================================================================="
echo "Base URL: ${BASE_URL}"
echo ""

# Test 1: Health
info "[Test 1] GET /health"
HTTP=$(curl -s -o /tmp/ws_test_body -w "%{http_code}" "${BASE_URL}/health" 2>/dev/null || echo "000")
BODY=$(cat /tmp/ws_test_body 2>/dev/null || true)
if [ "$HTTP" = "200" ] && echo "$BODY" | grep -q '"status"'; then
    pass "Health returned 200 with status"
else
    fail "Health failed (HTTP $HTTP)"
    [ -n "$BODY" ] && echo "       Body: ${BODY:0:200}"
fi
echo ""

# Test 2: Ready
info "[Test 2] GET /ready"
HTTP=$(curl -s -o /tmp/ws_test_body -w "%{http_code}" "${BASE_URL}/ready" 2>/dev/null || echo "000")
BODY=$(cat /tmp/ws_test_body 2>/dev/null || true)
if [ "$HTTP" = "200" ]; then
    pass "Ready returned 200"
    echo "$BODY" | grep -q "tools_count" && echo "       (tools_count present)"
elif [ "$HTTP" = "503" ]; then
    pass "Ready returned 503 (catalog not configured or degraded — acceptable for test)"
else
    fail "Ready returned unexpected HTTP $HTTP"
    [ -n "$BODY" ] && echo "       Body: ${BODY:0:200}"
fi
echo ""

# Test 3: List tools
info "[Test 3] GET /api/v1/tools"
HTTP=$(curl -s -o /tmp/ws_test_body -w "%{http_code}" "${BASE_URL}/api/v1/tools" 2>/dev/null || echo "000")
BODY=$(cat /tmp/ws_test_body 2>/dev/null || true)
if [ "$HTTP" = "200" ]; then
    if echo "$BODY" | grep -q '"tools"'; then
        pass "List tools returned 200 with tools array"
        COUNT=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('tools',[])))" 2>/dev/null || echo "0")
        echo "       (tools count: $COUNT)"
    else
        fail "List tools 200 but no 'tools' key"
    fi
elif [ "$HTTP" = "503" ]; then
    pass "List tools returned 503 (no catalog — acceptable if catalog not set)"
else
    fail "List tools failed (HTTP $HTTP)"
    [ -n "$BODY" ] && echo "       Body: ${BODY:0:300}"
fi
echo ""

# Test 4: Search tools
info "[Test 4] GET /api/v1/tools/search?q=naabu"
HTTP=$(curl -s -o /tmp/ws_test_body -w "%{http_code}" "${BASE_URL}/api/v1/tools/search?q=naabu" 2>/dev/null || echo "000")
BODY=$(cat /tmp/ws_test_body 2>/dev/null || true)
if [ "$HTTP" = "200" ]; then
    if echo "$BODY" | grep -q '"tools"'; then
        pass "Search returned 200 with tools array"
    else
        fail "Search 200 but no 'tools' key"
    fi
elif [ "$HTTP" = "503" ]; then
    pass "Search returned 503 (no catalog — acceptable)"
else
    fail "Search failed (HTTP $HTTP)"
fi
echo ""

# Test 5: OpenAPI docs (optional)
info "[Test 5] GET /docs (OpenAPI UI)"
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/docs" 2>/dev/null || echo "000")
if [ "$HTTP" = "200" ]; then
    pass "Docs page returns 200"
else
    fail "Docs returned HTTP $HTTP"
fi
echo ""

# Summary
echo "================================================================================="
echo -e "${BLUE}Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "================================================================================="
[ $FAIL -gt 0 ] && exit 1 || exit 0
