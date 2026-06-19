#!/usr/bin/env bash
# Test script for AI-Infra-Guard MCP Server
# Tests MCP protocol compliance via JSON-RPC (stdio and HTTP streamable).
# Writes full evidence to: ./test-results.txt (required for Hackerdogs MCP testing)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
IMAGE="hackerdogs/ai-infra-guard-mcp:latest"
PORT=8294
BINARY="ai-infra-guard"
CONTAINER_NAME="ai-infra-guard-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULT_FILE="${PROJECT_DIR}/test-results.txt"
MCP_TEST_RESULT_MAX_CHARS=${MCP_TEST_RESULT_MAX_CHARS:-200000}

pass() { echo -e "  ${GREEN}PASS: $1${NC}"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}FAIL: $1${NC}"; FAIL=$((FAIL + 1)); }
info() { echo -e "${BLUE}$1${NC}"; }

# Append one section to test-results.txt (truncate very large blobs; same pattern as scripts/mcp-standard-six-test.sh)
append_section() {
  local title="$1"
  local status="$2"
  local body="$3"
  {
    echo ""
    echo "================================================================================="
    echo "$title"
    echo "Status: $status"
    echo "---------------------------------------------------------------------------------"
    if [ "${MCP_TEST_RESULT_MAX_CHARS}" = "0" ] || [ -z "${MCP_TEST_RESULT_MAX_CHARS}" ]; then
      printf '%s\n' "$body"
    else
      python -c "
import sys
maxc = int(sys.argv[1])
raw = sys.stdin.read()
n = len(raw)
if maxc <= 0 or n <= maxc:
    sys.stdout.write(raw)
else:
    sys.stdout.write(f'[truncated: showing last {maxc} of {n} characters]\n')
    sys.stdout.write(raw[-maxc:])
" "${MCP_TEST_RESULT_MAX_CHARS}" <<<"$body"
    fi
    echo "---------------------------------------------------------------------------------"
  } >>"$RESULT_FILE"
}

cleanup() {
  docker stop "$CONTAINER_NAME" 2>/dev/null || true
  docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
}
trap cleanup EXIT

{
  echo "AI-Infra-Guard MCP — test evidence"
  echo "Generated (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Image: ${IMAGE}"
  echo "HTTP port: ${PORT}"
  echo "Container (HTTP): ${CONTAINER_NAME}"
  echo ""
  echo "Below: raw outputs from each step (not only PASS/FAIL)."
} >"$RESULT_FILE"

echo "================================================================================="
echo -e "${BLUE}AI-Infra-Guard MCP Server — Test Suite${NC}"
echo -e "Evidence file: ${BLUE}${RESULT_FILE}${NC}"
echo "================================================================================="
echo ""

# --- Test 1: Docker image ---
info "[Test 1] Docker image"
S1=FAIL
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
  BUILD_LOG="(Image ${IMAGE} already present locally — docker build was skipped.)

$(docker image inspect "$IMAGE" --format 'Id={{.Id}}
Created={{.Created}}
Size={{.Size}}
Architecture={{.Architecture}}' 2>&1)"
  pass "Docker image $IMAGE exists"
  S1=PASS
else
  echo "  Image not found. Building..."
  set +e
  BUILD_LOG=$(docker build -t "$IMAGE" "$PROJECT_DIR" 2>&1)
  BRC=$?
  set -e
  if [ "$BRC" -eq 0 ]; then
    pass "Docker image $IMAGE built"
    S1=PASS
  else
    fail "Docker image $IMAGE could not be built"
  fi
fi
append_section "[Test 1] Docker image" "$S1" "$BUILD_LOG"
[ "$S1" = "FAIL" ] && exit 1
echo ""

# --- Test 2: CLI binary ---
info "[Test 2] CLI binary inside container"
S2=FAIL
set +e
BINARY_FULL=$(docker run --rm "$IMAGE" "$BINARY" --help 2>&1)
if [ -z "$BINARY_FULL" ]; then
  BINARY_FULL=$(docker run --rm "$IMAGE" "$BINARY" --version 2>&1)
fi
if [ -z "$BINARY_FULL" ]; then
  BINARY_FULL=$(docker run --rm "$IMAGE" "$BINARY" -h 2>&1)
fi
set -e
if [ -n "$BINARY_FULL" ]; then
  pass "$BINARY binary responds"
  echo "       ${BINARY_FULL%%$'\n'*}"
  S2=PASS
else
  fail "$BINARY binary not found or not responding"
  BINARY_FULL="(no output from --help, --version, or -h)"
fi
append_section "[Test 2] CLI binary (docker run ... $BINARY --help)" "$S2" "$BINARY_FULL"
echo ""

# --- Test 3: stdio MCP ---
info "[Test 3] MCP stdio mode — initialize + tools/list"
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test-client","version":"1.0.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

S3=FAIL
STDIO_OUT=$(python "$PROJECT_DIR/../scripts/mcp_stdio_docker_tools_list.py" "$IMAGE") || true

if grep -q '"tools"' <<< "$STDIO_OUT"; then
  TOOL_COUNT=$(echo "$STDIO_OUT" | grep -o '"name"' | wc -l | tr -d ' ')
  pass "stdio mode returned tools/list response ($TOOL_COUNT tool names found)"
  S3=PASS
else
  fail "stdio mode did not return a valid tools/list response"
  [ -n "$STDIO_OUT" ] && echo "       Response preview: ${STDIO_OUT:0:300}"
fi
append_section "[Test 3] MCP stdio — full docker stdout/stderr" "$S3" "$STDIO_OUT"
echo ""

# --- Test 4–6: HTTP ---
info "[Test 4] MCP HTTP streamable mode — initialize"
cleanup
docker run -d --name "$CONTAINER_NAME" \
  -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT \
  -p "$PORT:$PORT" "$IMAGE" >/dev/null

SESSION_ID=""
INIT_RESP=""
MAX_WAIT=30
WAITED=0
while [ "$WAITED" -lt "$MAX_WAIT" ]; do
  INIT_RESP=$(curl -s -D /tmp/mcp_headers -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$INIT_REQ" 2>/dev/null) && break
  sleep 2
  WAITED=$((WAITED + 2))
done

HTTP_CODE=$(head -1 /tmp/mcp_headers 2>/dev/null | grep -o '[0-9]\{3\}' | head -1 || echo "000")
SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_headers 2>/dev/null | sed 's/.*: //' | tr -d '\r' || true)

S4=FAIL
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "202" ]; then
  pass "HTTP streamable mode responded (status $HTTP_CODE)"
  [ -n "$SESSION_ID" ] && echo "       Session ID: ${SESSION_ID:0:16}..."
  S4=PASS
else
  fail "HTTP streamable mode did not respond (status $HTTP_CODE after ${WAITED}s)"
  docker logs "$CONTAINER_NAME" 2>&1 | tail -10
fi
append_section "[Test 4] HTTP initialize — headers + body + docker logs (tail)" "$S4" "--- Response headers (initialize) ---
$(cat /tmp/mcp_headers 2>/dev/null || true)

--- Response body (initialize) ---
${INIT_RESP}

--- docker logs (last 80 lines) ---
$(docker logs "$CONTAINER_NAME" 2>&1 | tail -80)"
echo ""

info "[Test 5] MCP HTTP — tools/list"
SESSION_HDR=()
if [ -n "$SESSION_ID" ]; then
  SESSION_HDR=( -H "mcp-session-id: $SESSION_ID" )
fi

curl -s -X POST "http://localhost:${PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  "${SESSION_HDR[@]}" \
  -d "$INIT_NOTIF" >/dev/null 2>&1 || true

S5=FAIL
TOOLS_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  "${SESSION_HDR[@]}" \
  -d "$LIST_REQ" 2>/dev/null || true)

if echo "$TOOLS_RESP" | grep -q '"tools"'; then
  pass "HTTP tools/list returned tools"
  echo "$TOOLS_RESP" | python -c "
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
    except Exception:
        pass
" 2>/dev/null || true
  S5=PASS
else
  fail "HTTP tools/list did not return tools"
  [ -n "$TOOLS_RESP" ] && echo "       Response: ${TOOLS_RESP:0:300}"
fi
append_section "[Test 5] HTTP tools/list — raw response" "$S5" "$TOOLS_RESP"
echo ""

info "[Test 6] MCP HTTP — tools/call (run_ai_infra_guard)"
CALL_REQ='{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"run_ai_infra_guard","arguments":{"arguments":"--help"}}}'
S6=FAIL
CALL_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  "${SESSION_HDR[@]}" \
  -d "$CALL_REQ" 2>/dev/null || true)

if echo "$CALL_RESP" | grep -q '"result"'; then
  pass "tools/call run_ai_infra_guard returned a result"
  S6=PASS
elif echo "$CALL_RESP" | grep -q '"content"'; then
  pass "tools/call run_ai_infra_guard returned content"
  S6=PASS
else
  fail "tools/call run_ai_infra_guard did not return expected response"
  [ -n "$CALL_RESP" ] && echo "       Response: ${CALL_RESP:0:500}"
fi
append_section "[Test 6] HTTP tools/call — request JSON + raw response" "$S6" "--- tools/call request ---
${CALL_REQ}

--- tools/call response ---
${CALL_RESP}"
echo ""

{
  echo ""
  echo "================================================================================="
  echo "SUMMARY"
  echo "================================================================================="
  echo "Steps passed: $PASS  Steps failed: $FAIL"
  echo "Overall: $([ "$FAIL" -eq 0 ] && echo PASS || echo FAIL)"
  echo "================================================================================="
} >>"$RESULT_FILE"

echo "================================================================================="
echo -e "${BLUE}Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo -e "Evidence: ${RESULT_FILE}"
echo "================================================================================="
[ "$FAIL" -gt 0 ] && exit 1 || exit 0
