#!/bin/bash
# Test script for VirusTotal MCP Server
# Tests MCP protocol compliance via JSON-RPC (stdio and HTTP streamable)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
IMAGE="hackerdogs/virustotal-mcp:latest"
PORT=8369
CONTAINER_NAME="virustotal-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

pass() { echo -e "  ${GREEN}✅ PASS: $1${NC}"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}❌ FAIL: $1${NC}"; FAIL=$((FAIL + 1)); }
info() { echo -e "${BLUE}$1${NC}"; }

cleanup() {
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}
trap cleanup EXIT

echo "================================================================================="
echo -e "${BLUE}VirusTotal MCP Server — Test Suite${NC}"
echo "================================================================================="
echo ""

# Test 1: Verify Docker image exists (build separately: docker build -t $IMAGE $PROJECT_DIR)
info "[Test 1] Docker image"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Build first: docker build -t $IMAGE $PROJECT_DIR" >&2
  exit 1
fi
pass "Docker image $IMAGE exists"
echo ""

# Test 2: Python requests library available
info "[Test 2] Python requests library inside container"
REQUESTS_OUTPUT=$(docker run --rm "$IMAGE" python -c "import requests; print(f'requests {requests.__version__}')" 2>&1 || true)
if echo "$REQUESTS_OUTPUT" | grep -q "requests"; then
    pass "requests library available"
    echo "       $REQUESTS_OUTPUT"
else
    fail "requests library not found"
fi
echo ""

# Test 3: MCP stdio mode — initialize + tools/list
info "[Test 3] MCP stdio mode — initialize + tools/list"
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

STDIO_OUT=$(printf '%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$LIST_REQ" | \
    docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null || true)

if echo "$STDIO_OUT" | grep -q '"tools"'; then
    TOOL_COUNT=$(echo "$STDIO_OUT" | grep -o '"name"' | wc -l)
    pass "stdio mode returned tools/list response ($TOOL_COUNT tool names found)"
else
    fail "stdio mode did not return a valid tools/list response"
    [ -n "$STDIO_OUT" ] && echo "       Response preview: ${STDIO_OUT:0:300}"
fi
echo ""

# Test 4: MCP HTTP streamable mode — initialize
info "[Test 4] MCP HTTP streamable mode — initialize"
cleanup
docker run -d --name "$CONTAINER_NAME" \
    -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT \
    -p "$PORT:$PORT" "$IMAGE" > /dev/null

SESSION_ID=""
MAX_WAIT=30; WAITED=0
while [ $WAITED -lt $MAX_WAIT ]; do
    INIT_RESP=$(curl -s -D /tmp/mcp_headers -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "$INIT_REQ" 2>/dev/null) && break
    sleep 2; WAITED=$((WAITED + 2))
done

HTTP_CODE=$(head -1 /tmp/mcp_headers 2>/dev/null | grep -o '[0-9]\{3\}' | head -1 || echo "000")
SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_headers 2>/dev/null | sed 's/.*: //' | tr -d '\r' || true)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
    pass "HTTP streamable mode responded (status $HTTP_CODE)"
    [ -n "$SESSION_ID" ] && echo "       Session ID: ${SESSION_ID:0:16}..."
else
    fail "HTTP streamable mode did not respond (status $HTTP_CODE after ${WAITED}s)"
    docker logs "$CONTAINER_NAME" 2>&1 | tail -10
fi
echo ""

# Test 5: MCP HTTP — tools/list
info "[Test 5] MCP HTTP — tools/list"
SESSION_HDR=""
[ -n "$SESSION_ID" ] && SESSION_HDR="-H mcp-session-id:${SESSION_ID}"

curl -s -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    $SESSION_HDR \
    -d "$INIT_NOTIF" > /dev/null 2>&1 || true

TOOLS_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    $SESSION_HDR \
    -d "$LIST_REQ" 2>/dev/null || true)

if echo "$TOOLS_RESP" | grep -q '"tools"'; then
    pass "HTTP tools/list returned tools"
    echo "$TOOLS_RESP" | python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if line.startswith('data: '): line = line[6:]
    if not line: continue
    try:
        data = json.loads(line)
        tools = data.get('result',{}).get('tools',[])
        for t in tools:
            print(f'       - {t[\"name\"]}: {t.get(\"description\",\"\")[:80]}')
    except: pass
" 2>/dev/null || true
else
    fail "HTTP tools/list did not return tools"
    [ -n "$TOOLS_RESP" ] && echo "       Response: ${TOOLS_RESP:0:300}"
fi
echo ""

# Test 6: MCP HTTP — tools/call (vt_domain_report — expect API key error)
info "[Test 6] MCP HTTP — tools/call (vt_domain_report)"
CALL_REQ='{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"vt_domain_report","arguments":{"domain":"example.com"}}}'
CALL_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    $SESSION_HDR \
    -d "$CALL_REQ" 2>/dev/null || true)

if echo "$CALL_RESP" | grep -q '"result"'; then
    pass "tools/call vt_domain_report returned a result"
elif echo "$CALL_RESP" | grep -q '"content"'; then
    pass "tools/call vt_domain_report returned content"
elif echo "$CALL_RESP" | grep -q 'VT_API_KEY'; then
    pass "tools/call vt_domain_report returned expected API key error"
else
    fail "tools/call vt_domain_report did not return expected response"
    [ -n "$CALL_RESP" ] && echo "       Response: ${CALL_RESP:0:500}"
fi
echo ""

# Summary
echo "================================================================================="
echo -e "${BLUE}Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "================================================================================="
[ $FAIL -gt 0 ] && exit 1 || exit 0
