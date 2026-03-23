#!/bin/bash
# MCP server test compliance: 1=install, 2=stdio tools/list, 3=stdio tools/call, 4=HTTP tools/list, 5=HTTP tools/call
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0
IMAGE="hackerdogs/nmap-mcp:latest"
PORT=8390
CONTAINER_NAME="nmap-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pass() { echo -e "  ${GREEN}PASS: $1${NC}"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL: $1${NC}"; FAIL=$((FAIL+1)); }
info() { echo -e "${BLUE}$1${NC}"; }
cleanup() { docker stop "$CONTAINER_NAME" 2>/dev/null || true; docker rm -f "$CONTAINER_NAME" 2>/dev/null || true; }
trap cleanup EXIT
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
CALL_REQ='{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_nmap","arguments":{"arguments":"-h"}}}'
echo "========== nmap-mcp test (compliance) =========="
info "[1] Install"
docker build -t "$IMAGE" "$PROJECT_DIR" 2>/dev/null || true
docker image inspect "$IMAGE" >/dev/null 2>&1 && pass "image exists" || { fail "image build"; exit 1; }
info "[2] Stdio tools/list"
STDIO_OUT=$(python3 "$PROJECT_DIR/../scripts/mcp_stdio_docker_tools_list.py" "$IMAGE") || true
echo "$STDIO_OUT" | grep -q '"tools"' && pass "stdio tools/list" || fail "stdio tools/list"
info "[3] Stdio tools/call run_nmap"
CALL_OUT=$( ( printf '%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$CALL_REQ"; sleep 5 ) | docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null) || true
echo "$CALL_OUT" | grep -q 'result\|content' && pass "stdio tools/call run_nmap" || fail "stdio tools/call run_nmap"
info "[4] HTTP streamable tools/list"
cleanup
docker run -d --name "$CONTAINER_NAME" -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT -p "$PORT:$PORT" "$IMAGE" >/dev/null
sleep 5
SESSION_ID=""; WAITED=0; TOOLS_RESP=""; SESS_HDR=""
while [ "$WAITED" -lt "${MCP_HTTP_LIST_MAX_WAIT:-30}" ]; do
  curl -s -D /tmp/mcp_h -o /dev/null -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$INIT_REQ" 2>/dev/null || true
  SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_h 2>/dev/null | sed 's/.*: *//' | tr -d '\r' | head -1)
  SESS_HDR=""; [ -n "$SESSION_ID" ] && SESS_HDR="-H mcp-session-id:$SESSION_ID"
  curl -s -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" $SESS_HDR -d "$INIT_NOTIF" >/dev/null 2>&1 || true
  TOOLS_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" $SESS_HDR -d "$LIST_REQ" 2>/dev/null) || true
  if echo "$TOOLS_RESP" | grep -q '"tools"'; then break; fi
  sleep 3; WAITED=$((WAITED+3))
done
echo "$TOOLS_RESP" | grep -q '"tools"' && pass "HTTP tools/list" || fail "HTTP tools/list"
info "[5] HTTP streamable tools/call run_nmap"
CALL_HTTP=$(curl -s -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" $SESS_HDR -d "$CALL_REQ" 2>/dev/null) || true
echo "$CALL_HTTP" | grep -q 'result\|content' && pass "HTTP tools/call run_nmap" || fail "HTTP tools/call run_nmap"
echo ""; echo "Total: $PASS passed, $FAIL failed"; [ $FAIL -gt 0 ] && exit 1; exit 0
