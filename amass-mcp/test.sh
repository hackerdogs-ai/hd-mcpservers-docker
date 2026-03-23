#!/bin/bash
# MCP server test compliance
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0
IMAGE="hackerdogs/amass-mcp:latest"
PORT=8382
CONTAINER_NAME="amass-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pass() { echo -e "  ${GREEN}PASS: $1${NC}"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL: $1${NC}"; FAIL=$((FAIL+1)); }
info() { echo -e "${BLUE}$1${NC}"; }
cleanup() { docker stop "$CONTAINER_NAME" 2>/dev/null || true; docker rm -f "$CONTAINER_NAME" 2>/dev/null || true; }
trap cleanup EXIT
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
CALL_REQ='{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_amass","arguments":{"arguments":"-h"}}}'
echo "========== amass-mcp test =========="
info "[1] Install"
docker build -t "$IMAGE" "$PROJECT_DIR" 2>/dev/null || true
docker image inspect "$IMAGE" >/dev/null 2>&1 && pass "image" || { fail "image"; exit 1; }
info "[2] Stdio tools/list"
STDIO_OUT=$(python3 "$PROJECT_DIR/../scripts/mcp_stdio_docker_tools_list.py" "$IMAGE") || true
echo "$STDIO_OUT" | grep -q '"tools"' && pass "stdio list" || fail "stdio list"
info "[3] Stdio tools/call"
CALL_OUT=$( ( printf '%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$CALL_REQ"; sleep 5 ) | docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null) || true
echo "$CALL_OUT" | grep -q 'result\|content' && pass "stdio call" || fail "stdio call"
info "[4] HTTP tools/list"
cleanup
docker run -d --name "$CONTAINER_NAME" -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT -p "$PORT:$PORT" "$IMAGE" >/dev/null
sleep 5
SESS_HDR=""
for i in $(seq 1 10); do
  curl -s -D /tmp/mcp_h -o /dev/null -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$INIT_REQ" 2>/dev/null || true
  SID=$(grep -i mcp-session-id /tmp/mcp_h 2>/dev/null | sed 's/.*: *//' | tr -d '\r' | head -1)
  [ -n "$SID" ] && SESS_HDR="-H mcp-session-id:$SID"
  curl -s -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" $SESS_HDR -d "$INIT_NOTIF" >/dev/null 2>&1
  TOOLS=$(curl -s -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" $SESS_HDR -d "$LIST_REQ" 2>/dev/null)
  echo "$TOOLS" | grep -q '"tools"' && break
  sleep 2
done
echo "$TOOLS" | grep -q '"tools"' && pass "HTTP list" || fail "HTTP list"
info "[5] HTTP tools/call"
CALL_HTTP=$(curl -s -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" $SESS_HDR -d "$CALL_REQ" 2>/dev/null) || true
echo "$CALL_HTTP" | grep -q 'result\|content' && pass "HTTP call" || fail "HTTP call"
echo ""; echo "Total: $PASS passed, $FAIL failed"; [ $FAIL -gt 0 ] && exit 1; exit 0
