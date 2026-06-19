#!/bin/bash
# MCP server test compliance: stdio tools/list, stdio tools/call, HTTP tools/list, HTTP tools/call
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0
IMAGE="hackerdogs/httpx-mcp:latest"
PORT=8386
CONTAINER_NAME="httpx-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$PROJECT_DIR/../scripts/mcp_compliance_python.sh"
MCP_HDR_FILE="${TMPDIR:-/tmp}/mcp_http_${CONTAINER_NAME}.$$"

pass() { echo -e "  ${GREEN}PASS: $1${NC}"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL: $1${NC}"; FAIL=$((FAIL+1)); }
info() { echo -e "${BLUE}$1${NC}"; }
cleanup() {
  docker stop "$CONTAINER_NAME" 2>/dev/null || true
  docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
  rm -f "$MCP_HDR_FILE" 2>/dev/null || true
}
trap cleanup EXIT

INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
CALL_REQ='{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_httpx","arguments":{"arguments":"-h"}}}'

echo "========== httpx-mcp test (compliance) =========="
info "[1] Install"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  docker build -t "$IMAGE" "$PROJECT_DIR" || { fail "image build"; exit 1; }
fi
docker image inspect "$IMAGE" >/dev/null 2>&1 && pass "image exists" || { fail "image missing"; exit 1; }

info "[2] Stdio tools/list"
if "$MCP_PYTHON" "$PROJECT_DIR/../scripts/mcp_stdio_docker_tools_list.py" --check "$IMAGE" 2>/dev/null; then
  pass "stdio tools/list"
else
  fail "stdio tools/list"
fi

info "[3] Stdio tools/call run_httpx"
CALL_OUT=$( ( printf '%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$CALL_REQ"; sleep 5 ) | docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null) || true
echo "$CALL_OUT" | grep -q 'result\|content' && pass "stdio tools/call run_httpx" || fail "stdio tools/call run_httpx"

info "[4] HTTP streamable tools/list"
cleanup
docker run -d --name "$CONTAINER_NAME" -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT -p "$PORT:$PORT" "$IMAGE" >/dev/null
sleep "${MCP_HTTP_STARTUP_SLEEP:-10}"

SESSION_ID=""; WAITED=0; TOOLS_RESP=""
while [ "$WAITED" -lt "${MCP_HTTP_LIST_MAX_WAIT:-45}" ]; do
  : >"$MCP_HDR_FILE"
  curl -s -D "$MCP_HDR_FILE" -o /dev/null -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
    -d "$INIT_REQ" 2>/dev/null || true
  SESSION_ID=$(grep -i 'mcp-session-id' "$MCP_HDR_FILE" 2>/dev/null | sed 's/.*:[[:space:]]*//' | tr -d '\r' | head -1 || true)
  SESSION_HDR=()
  [ -n "$SESSION_ID" ] && SESSION_HDR=(-H "Mcp-Session-Id: ${SESSION_ID}")
  curl -s -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
    "${SESSION_HDR[@]}" -d "$INIT_NOTIF" >/dev/null 2>&1 || true
  TOOLS_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
    "${SESSION_HDR[@]}" -d "$LIST_REQ" 2>/dev/null) || true
  if echo "$TOOLS_RESP" | grep -q '"tools"'; then break; fi
  sleep 3; WAITED=$((WAITED+3))
done
echo "$TOOLS_RESP" | grep -q '"tools"' && pass "HTTP tools/list" || fail "HTTP tools/list"

info "[5] HTTP streamable tools/call run_httpx"
SESSION_HDR=()
[ -n "$SESSION_ID" ] && SESSION_HDR=(-H "Mcp-Session-Id: ${SESSION_ID}")
CALL_HTTP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
  -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \
  "${SESSION_HDR[@]}" -d "$CALL_REQ" 2>/dev/null) || true
echo "$CALL_HTTP" | grep -q 'result\|content' && pass "HTTP tools/call run_httpx" || fail "HTTP tools/call run_httpx"

echo ""; echo "Total: $PASS passed, $FAIL failed"
[ $FAIL -gt 0 ] && exit 1
exit 0
