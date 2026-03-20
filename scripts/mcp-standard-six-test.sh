#!/usr/bin/env bash
#
# Standard 6-step MCP Docker test (used by each */test.sh).
#
# Writes evidence to:  ${MCP_PROJECT_DIR}/test-results.txt
# (full outputs from build, stdio, HTTP calls — not only PASS/FAIL)
#
# Optional:
#   MCP_TEST_RESULT_MAX_CHARS  max characters per section (default 200000); 0 = unlimited
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MCP_VALIDATE_TOOLS_CALL="${SCRIPT_DIR}/mcp-validate-tools-call-output.py"

: "${MCP_IMAGE:?Set MCP_IMAGE}"
: "${MCP_PORT:?Set MCP_PORT}"
: "${MCP_CONTAINER:?Set MCP_CONTAINER}"
: "${MCP_TOOL_NAME:?Set MCP_TOOL_NAME}"
: "${MCP_TOOL_ARGUMENTS:?Set MCP_TOOL_ARGUMENTS (JSON object for tool arguments)}"

MCP_EXTRA_DOCKER_ARGS=${MCP_EXTRA_DOCKER_ARGS:-}
MCP_TEST_RESULT_MAX_CHARS=${MCP_TEST_RESULT_MAX_CHARS:-200000}

: "${MCP_PROJECT_DIR:?Set MCP_PROJECT_DIR to the MCP server directory (Dockerfile dir)}"

RESULT_FILE="${MCP_PROJECT_DIR}/test-results.txt"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}[FAIL]${NC} $1"; FAIL=$((FAIL + 1)); }
info() { echo -e "${BLUE}$1${NC}"; }

# Append one section to test-results.txt (truncate very large blobs)
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
      python3 -c "
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

INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"mcp-standard-test","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

export MCP_TOOL_NAME MCP_TOOL_ARGUMENTS
CALL_REQ=$(python3 -c "import json,os; n=os.environ['MCP_TOOL_NAME']; a=json.loads(os.environ['MCP_TOOL_ARGUMENTS']); print(json.dumps({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':n,'arguments':a}}))")

http_cleanup() {
  docker stop "$MCP_CONTAINER" 2>/dev/null || true
  docker rm -f "$MCP_CONTAINER" 2>/dev/null || true
}

trap http_cleanup EXIT

# --- Initialize evidence file ---
{
  echo "MCP standard 6-step test - evidence"
  echo "Generated (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Image: ${MCP_IMAGE}"
  echo "HTTP port: ${MCP_PORT}"
  echo "Container (HTTP): ${MCP_CONTAINER}"
  echo "Tool exercised: ${MCP_TOOL_NAME}"
  echo "Tool arguments (JSON): ${MCP_TOOL_ARGUMENTS}"
  echo ""
  echo "Below: raw outputs from each step (not only PASS/FAIL)."
} >"$RESULT_FILE"

echo "================================================================================="
echo -e "${BLUE}MCP standard 6-step test${NC}  image=${MCP_IMAGE}  port=${MCP_PORT}"
echo -e "Evidence file: ${BLUE}${RESULT_FILE}${NC}"
echo "================================================================================="
echo ""

# --- Step 1: build / install ---
info "[1/6] Install - docker build"
set +e
BUILD_LOG=$(docker build -t "$MCP_IMAGE" "$MCP_PROJECT_DIR" 2>&1)
BUILD_RC=$?
set -e
if [ "$BUILD_RC" -eq 0 ]; then
  pass "docker build -t $MCP_IMAGE"
  append_section "[1/6] Install - docker build" "PASS" "$BUILD_LOG"
else
  fail "docker build"
  append_section "[1/6] Install - docker build" "FAIL" "$BUILD_LOG"
  exit 1
fi
echo ""

# --- Step 2: stdio tools/list ---
info "[2/6] List tools (stdio)"
# shellcheck disable=SC2086
STDIO_LIST=$(printf '%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$LIST_REQ" | docker run -i --rm -e MCP_TRANSPORT=stdio $MCP_EXTRA_DOCKER_ARGS "$MCP_IMAGE" 2>&1) || STDIO_LIST="${STDIO_LIST:-}(docker run failed)"
S2=FAIL
if echo "$STDIO_LIST" | grep -q '"tools"'; then
  pass "stdio tools/list"
  S2=PASS
else
  fail "stdio tools/list"
  echo "$STDIO_LIST" | tail -5
fi
append_section "[2/6] List tools (stdio - full docker stdout/stderr)" "$S2" "$STDIO_LIST"
echo ""

# --- Step 3: stdio tools/call ---
info "[3/6] Run tool (stdio) - $MCP_TOOL_NAME"
# shellcheck disable=SC2086
STDIO_CALL=$(printf '%s\n%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$LIST_REQ" "$CALL_REQ" | docker run -i --rm -e MCP_TRANSPORT=stdio $MCP_EXTRA_DOCKER_ARGS "$MCP_IMAGE" 2>&1) || STDIO_CALL="${STDIO_CALL:-}(docker run failed)"
S3=FAIL
set +e
V3_MSG=$(printf '%s' "$STDIO_CALL" | python3 "$MCP_VALIDATE_TOOLS_CALL" 3 2>&1)
V3_RC=$?
set -e
if [ "$V3_RC" -eq 0 ]; then
  pass "stdio tools/call succeeded (strict validation, id=3)"
  S3=PASS
else
  fail "stdio tools/call failed validation: $V3_MSG"
  echo "$STDIO_CALL" | tail -20
fi
append_section "[3/6] Run tool (stdio) - tools/call full output" "$S3" "$STDIO_CALL"
echo ""

# --- Step 4–5: HTTP streamable ---
info "[4/6] List tools (HTTP streamable)"
http_cleanup
# shellcheck disable=SC2086
docker run -d --name "$MCP_CONTAINER" \
  -e MCP_TRANSPORT=streamable-http -e MCP_PORT="$MCP_PORT" \
  -p "${MCP_PORT}:${MCP_PORT}" \
  $MCP_EXTRA_DOCKER_ARGS \
  "$MCP_IMAGE" >/dev/null

HTTP_STARTUP_WAIT=${HTTP_STARTUP_WAIT:-20}
sleep "$HTTP_STARTUP_WAIT"

SESSION_ID=""
TOOLS_RESP=""
HTTP_INIT_META=""
WAITED=0
while [ "$WAITED" -lt 45 ]; do
  curl -s --max-time 15 -D /tmp/mcp_std_hdr -o /tmp/mcp_std_body -X POST "http://localhost:${MCP_PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$INIT_REQ" 2>/dev/null || true
  SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_std_hdr 2>/dev/null | head -1 | cut -d: -f2- | tr -d '\r' | sed 's/^ //') || true
  HTTP_INIT_META="--- Response headers (initialize) ---
$(cat /tmp/mcp_std_hdr 2>/dev/null || true)
--- Response body (initialize) ---
$(cat /tmp/mcp_std_body 2>/dev/null || true)"
  SESS_HDR=()
  if [ -n "$SESSION_ID" ]; then
    SESS_HDR=( -H "mcp-session-id: $SESSION_ID" )
  fi
  curl -s --max-time 10 -X POST "http://localhost:${MCP_PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    "${SESS_HDR[@]}" \
    -d "$INIT_NOTIF" >/dev/null 2>&1 || true
  TOOLS_RESP=$(curl -s --max-time 15 -X POST "http://localhost:${MCP_PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    "${SESS_HDR[@]}" \
    -d "$LIST_REQ" 2>/dev/null) || true
  if echo "$TOOLS_RESP" | grep -q '"tools"'; then
    break
  fi
  sleep 3
  WAITED=$((WAITED + 3))
done

S4=FAIL
if echo "$TOOLS_RESP" | grep -q '"tools"'; then
  pass "HTTP streamable tools/list"
  S4=PASS
else
  fail "HTTP streamable tools/list"
  docker logs "$MCP_CONTAINER" 2>&1 | tail -15
fi
append_section "[4/6] List tools (HTTP streamable) - init metadata + tools/list body" "$S4" "${HTTP_INIT_META}

--- tools/list response body ---
${TOOLS_RESP}

--- docker logs (last 80 lines) ---
$(docker logs "$MCP_CONTAINER" 2>&1 | tail -80)"
echo ""

info "[5/6] Run tool (HTTP streamable) - $MCP_TOOL_NAME"
HTTP_CALL_REQ=$(python3 -c "import json,os; n=os.environ['MCP_TOOL_NAME']; a=json.loads(os.environ['MCP_TOOL_ARGUMENTS']); print(json.dumps({'jsonrpc':'2.0','id':4,'method':'tools/call','params':{'name':n,'arguments':a}}))")
CALL_RESP=$(curl -s --max-time 60 -X POST "http://localhost:${MCP_PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  "${SESS_HDR[@]}" \
  -d "$HTTP_CALL_REQ" 2>/dev/null) || CALL_RESP=""

S5=FAIL
set +e
V5_MSG=$(printf '%s' "$CALL_RESP" | python3 "$MCP_VALIDATE_TOOLS_CALL" 4 2>&1)
V5_RC=$?
set -e
if [ "$V5_RC" -eq 0 ]; then
  pass "HTTP streamable tools/call succeeded (strict validation, id=4)"
  S5=PASS
else
  fail "HTTP streamable tools/call failed validation: $V5_MSG"
  echo "$CALL_RESP" | tail -20
fi
append_section "[5/6] Run tool (HTTP streamable) - request + full response" "$S5" "--- tools/call request JSON ---
${HTTP_CALL_REQ}

--- tools/call response (raw) ---
${CALL_RESP}"
echo ""

# --- Step 6: tear down (explicit + trap) ---
info "[6/6] Tear down - stop/remove container $MCP_CONTAINER"
http_cleanup
trap - EXIT
pass "container removed (or was not running)"
append_section "[6/6] Tear down" "PASS" "docker stop / docker rm -f ${MCP_CONTAINER} (executed)"
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
echo -e "${BLUE}Summary:${NC} ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo -e "Evidence: ${RESULT_FILE}"
echo "================================================================================="
[ "$FAIL" -gt 0 ] && exit 1
exit 0
