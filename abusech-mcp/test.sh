#!/bin/bash
# Test script for Abuse.ch MCP Server — stdio and HTTP streamable

set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0
IMAGE="hackerdogs/abusech-mcp:latest"
PORT=8373
CONTAINER_NAME="abusech-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pass() { echo -e "  ${GREEN}✅ PASS: $1${NC}"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}❌ FAIL: $1${NC}"; FAIL=$((FAIL + 1)); }
info() { echo -e "${BLUE}$1${NC}"; }
cleanup() { docker stop "$CONTAINER_NAME" 2>/dev/null || true; docker rm -f "$CONTAINER_NAME" 2>/dev/null || true; }
trap cleanup EXIT

echo "================================================================================="
echo -e "${BLUE}Abuse.ch MCP Server — Test Suite${NC}"
echo "================================================================================="

info "[Test 1] Docker image"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then docker build -t "$IMAGE" "$PROJECT_DIR"; fi
docker image inspect "$IMAGE" >/dev/null 2>&1 && pass "Image exists" || { fail "Image build failed"; exit 1; }

info "[Test 2] MCP stdio — initialize + tools/list"
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
STDIO_OUT=$(printf '%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$LIST_REQ" | docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null || true)
echo "$STDIO_OUT" | grep -q '"tools"' && pass "stdio tools/list OK" || fail "stdio tools/list failed"

info "[Test 3] MCP HTTP streamable"
cleanup
docker run -d --name "$CONTAINER_NAME" -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT -p "$PORT:$PORT" "$IMAGE" >/dev/null
WAITED=0; while [ $WAITED -lt 30 ]; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$INIT_REQ" 2>/dev/null) || CODE=000
  [ "$CODE" = "200" ] || [ "$CODE" = "202" ] && break; sleep 2; WAITED=$((WAITED+2))
done
[ "$CODE" = "200" ] || [ "$CODE" = "202" ] && pass "HTTP streamable responded ($CODE)" || fail "HTTP streamable failed (code $CODE)"
echo ""; echo "Total: $PASS passed, $FAIL failed"; [ $FAIL -gt 0 ] && exit 1; exit 0
