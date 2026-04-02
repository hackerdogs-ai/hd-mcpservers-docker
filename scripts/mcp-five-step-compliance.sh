#!/usr/bin/env bash
# Shared 5-step MCP Docker compliance test (batch 3 standard):
#   1) Image exists (pull or build)
#   2) Stdio - tools/list
#   3) Stdio - tools/call (one tool)
#   4) HTTP streamable - tools/list
#   5) HTTP streamable - tools/call (same tool)
#
# Required env:
#   MCP_FIVE_PROJECT_DIR   server dir (Dockerfile context)
#   MCP_FIVE_IMAGE         e.g. hackerdogs/foo:latest
#   MCP_FIVE_PORT          host/container MCP HTTP port
#   MCP_FIVE_CONTAINER     docker name for HTTP test
#   MCP_FIVE_TOOL_NAME     tool name for tools/call
#   MCP_FIVE_TOOL_ARGS_JSON  JSON object for tool arguments, e.g. {"arguments":"--help"}
#
# Optional:
#   MCP_FIVE_TITLE         banner title
#   MCP_FIVE_STDIO_SLEEP   seconds after stdin for stdio tools/call (default 6)
#   MCP_STDIO_DOCKER_TIMEOUT / MCP_STDIO_DOCKER_TIMEOUT_CALL
#   MCP_HTTP_STARTUP_SLEEP / MCP_HTTP_LIST_MAX_WAIT

set -eu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

: "${MCP_FIVE_PROJECT_DIR:?Set MCP_FIVE_PROJECT_DIR}"
: "${MCP_FIVE_IMAGE:?Set MCP_FIVE_IMAGE}"
: "${MCP_FIVE_PORT:?Set MCP_FIVE_PORT}"
: "${MCP_FIVE_CONTAINER:?Set MCP_FIVE_CONTAINER}"
: "${MCP_FIVE_TOOL_NAME:?Set MCP_FIVE_TOOL_NAME (or __AUTO__)}"
: "${MCP_FIVE_TOOL_ARGS_JSON:?Set MCP_FIVE_TOOL_ARGS_JSON}"

# shellcheck disable=SC1091
[ -f "$SCRIPT_DIR/prep_mcp_python_path.sh" ] && source "$SCRIPT_DIR/prep_mcp_python_path.sh"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/ensure_mcp_docker_image.sh"

TITLE="${MCP_FIVE_TITLE:-MCP server - 5-step compliance}"
STDIO_SLEEP="${MCP_FIVE_STDIO_SLEEP:-6}"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-180}"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'
PASS=0
FAIL=0
pass() { echo -e "  ${GREEN}PASS:${NC} $1"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}FAIL:${NC} $1"; FAIL=$((FAIL + 1)); }
info() { echo -e "${BLUE}$1${NC}"; }

INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"five-step","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

first_tool_name() {
  python3 - "$@" <<'PY'
import json, sys, re

raw = sys.stdin.read()
if not raw.strip():
    sys.exit(2)

# Accept either raw JSON or SSE lines like "data: {...}"
lines = []
for line in raw.splitlines():
    line = line.strip()
    if not line:
        continue
    if line.startswith("data: "):
        line = line[6:].strip()
    lines.append(line)

payloads = []
for line in lines:
    try:
        payloads.append(json.loads(line))
    except Exception:
        continue

# Search for tools list in any parsed JSON
for obj in payloads:
    tools = None
    if isinstance(obj, dict):
        tools = (obj.get("result") or {}).get("tools")
    if isinstance(tools, list) and tools:
        name = tools[0].get("name")
        if isinstance(name, str) and name:
            print(name)
            sys.exit(0)

# Last resort: regex scan
m = re.search(r'"name"\s*:\s*"([^"]+)"', raw)
if m:
    print(m.group(1))
    sys.exit(0)

sys.exit(3)
PY
}

make_call_req() {
  python3 - <<'PY'
import json, os
n = os.environ["MCP_FIVE_EFFECTIVE_TOOL_NAME"]
a = json.loads(os.environ["MCP_FIVE_TOOL_ARGS_JSON"])
req_id = int(os.environ.get("MCP_FIVE_CALL_ID", "3"))
print(json.dumps({"jsonrpc":"2.0","id":req_id,"method":"tools/call","params":{"name":n,"arguments":a}}))
PY
}

MCP_HDR="${TMPDIR:-/tmp}/mcp5_${MCP_FIVE_CONTAINER}_$$.hdr"

cleanup() {
  docker stop "$MCP_FIVE_CONTAINER" 2>/dev/null || true
  docker rm -f "$MCP_FIVE_CONTAINER" 2>/dev/null || true
  rm -f "$MCP_HDR" 2>/dev/null || true
}
trap cleanup EXIT

http_ok_body() {
  echo "$1" | grep -qE '"tools"' && return 0
  return 1
}

http_ok_call() {
  echo "$1" | grep -qE '"result"|"content"|"error"' && return 0
  return 1
}

stdio_ok_call() {
  echo "$1" | grep -qE '"result"|"content"|"error"' && return 0
  return 1
}

echo "================================================================================="
echo -e "${BLUE}${TITLE}${NC}"
echo "================================================================================="
echo ""

# --- Step 1 ---
info "[1/5] Docker image exists"
if ensure_mcp_docker_image "$MCP_FIVE_IMAGE" "$MCP_FIVE_PROJECT_DIR"; then
  pass "image $MCP_FIVE_IMAGE available"
else
  fail "could not pull or build $MCP_FIVE_IMAGE"
  exit 1
fi
echo ""

# --- Step 2 ---
info "[2/5] Stdio - tools/list"
STDIO_OUT=$(python3 "$SCRIPT_DIR/mcp_stdio_docker_tools_list.py" "$MCP_FIVE_IMAGE") || true
if echo "$STDIO_OUT" | grep -q '"tools"'; then
  pass "stdio tools/list"
else
  fail "stdio tools/list"
  [ -n "$STDIO_OUT" ] && echo "       ${STDIO_OUT:0:400}"
fi
echo ""

# --- Step 3 ---
MCP_FIVE_EFFECTIVE_TOOL_NAME="$MCP_FIVE_TOOL_NAME"
if [ "$MCP_FIVE_TOOL_NAME" = "__AUTO__" ]; then
  MCP_FIVE_EFFECTIVE_TOOL_NAME="$(printf '%s' "$STDIO_OUT" | first_tool_name || true)"
fi
if [ -z "$MCP_FIVE_EFFECTIVE_TOOL_NAME" ]; then
  MCP_FIVE_EFFECTIVE_TOOL_NAME="$MCP_FIVE_TOOL_NAME"
fi
export MCP_FIVE_EFFECTIVE_TOOL_NAME
export MCP_FIVE_CALL_ID=3
CALL_REQ_STDIO="$(make_call_req)"

info "[3/5] Stdio - tools/call ($MCP_FIVE_EFFECTIVE_TOOL_NAME)"
MCP_STDIO_BEFORE="${MCP_STDIO_DOCKER_TIMEOUT:-180}"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT_CALL:-120}"
CALL_OUT=$( ( printf '%s\n%s\n%s\n' "$INIT_REQ" "$INIT_NOTIF" "$CALL_REQ_STDIO"; sleep "$STDIO_SLEEP" ) | python3 "$SCRIPT_DIR/mcp_stdio_docker_pipe.py" "$MCP_FIVE_IMAGE" ) || true
export MCP_STDIO_DOCKER_TIMEOUT="$MCP_STDIO_BEFORE"
if stdio_ok_call "$CALL_OUT"; then
  pass "stdio tools/call"
else
  fail "stdio tools/call"
  echo "$CALL_OUT" | tail -12
fi
echo ""

# --- Step 4–5: HTTP ---
info "[4/5] HTTP streamable - tools/list"
cleanup
docker run -d --name "$MCP_FIVE_CONTAINER" \
  -e MCP_TRANSPORT=streamable-http -e MCP_PORT="$MCP_FIVE_PORT" \
  -p "${MCP_FIVE_PORT}:${MCP_FIVE_PORT}" \
  "$MCP_FIVE_IMAGE" >/dev/null

sleep "${MCP_HTTP_STARTUP_SLEEP:-20}"

SESSION_ID=""
WAITED=0
TOOLS_RESP=""
SESS_HDR=""
while [ "$WAITED" -lt "${MCP_HTTP_LIST_MAX_WAIT:-180}" ]; do
  curl -s --max-time 30 -D "$MCP_HDR" -o /dev/null -X POST "http://localhost:${MCP_FIVE_PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$INIT_REQ" 2>/dev/null || true
  SESSION_ID=$(grep -i 'mcp-session-id' "$MCP_HDR" 2>/dev/null | sed 's/.*: *//' | tr -d '\r' | head -1) || true
  SESS_HDR=""
  [ -n "$SESSION_ID" ] && SESS_HDR="-H mcp-session-id:${SESSION_ID}"
  curl -s --max-time 30 -X POST "http://localhost:${MCP_FIVE_PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    $SESS_HDR \
    -d "$INIT_NOTIF" >/dev/null 2>&1 || true
  TOOLS_RESP=$(curl -s --max-time 120 -X POST "http://localhost:${MCP_FIVE_PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    $SESS_HDR \
    -d "$LIST_REQ" 2>/dev/null) || true
  if http_ok_body "$TOOLS_RESP"; then break; fi
  sleep 3
  WAITED=$((WAITED + 3))
done

if http_ok_body "$TOOLS_RESP"; then
  pass "HTTP streamable tools/list"
else
  fail "HTTP streamable tools/list"
  docker logs "$MCP_FIVE_CONTAINER" 2>&1 | tail -15
fi
echo ""

MCP_FIVE_EFFECTIVE_TOOL_NAME_HTTP="$MCP_FIVE_EFFECTIVE_TOOL_NAME"
if [ "$MCP_FIVE_TOOL_NAME" = "__AUTO__" ]; then
  MCP_FIVE_EFFECTIVE_TOOL_NAME_HTTP="$(printf '%s' "$TOOLS_RESP" | first_tool_name || true)"
fi
if [ -z "$MCP_FIVE_EFFECTIVE_TOOL_NAME_HTTP" ]; then
  MCP_FIVE_EFFECTIVE_TOOL_NAME_HTTP="$MCP_FIVE_EFFECTIVE_TOOL_NAME"
fi
export MCP_FIVE_EFFECTIVE_TOOL_NAME="$MCP_FIVE_EFFECTIVE_TOOL_NAME_HTTP"
export MCP_FIVE_CALL_ID=4
CALL_REQ_HTTP="$(make_call_req)"

info "[5/5] HTTP streamable - tools/call ($MCP_FIVE_EFFECTIVE_TOOL_NAME_HTTP)"
CALL_HTTP=$(curl -s --max-time 120 -X POST "http://localhost:${MCP_FIVE_PORT}/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  $SESS_HDR \
  -d "$CALL_REQ_HTTP" 2>/dev/null) || true

if http_ok_call "$CALL_HTTP"; then
  pass "HTTP streamable tools/call"
else
  fail "HTTP streamable tools/call"
  echo "$CALL_HTTP" | tail -15
fi
echo ""

cleanup
trap - EXIT

echo "================================================================================="
echo -e "${BLUE}Results:${NC} ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "================================================================================="
[ "$FAIL" -gt 0 ] && exit 1
exit 0
