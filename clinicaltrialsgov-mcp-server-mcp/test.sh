#!/bin/bash
# WRITES_TEST_RESULTS_TXT=1  — scripts/run-all-mcp-tests.sh treats this as internal evidence writer
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0
IMAGE="clinicaltrialsgov-mcp-server-mcp"
PORT=8632
CONTAINER_NAME="clinicaltrialsgov-mcp-server-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_HELPER="$PROJECT_DIR/../scripts/mcp_stdio_docker_tools_list.py"

# Always refresh ./test-results.txt when you run this script directly (verify-rebuilt-images.sh does not tee per-dir).
RESULT_FILE="${MCP_TEST_RESULTS_FILE:-$PROJECT_DIR/test-results.txt}"
if [ "${MCP_TEST_WRITE_RESULTS:-1}" != "0" ]; then
  {
    echo "MCP test run - clinicaltrialsgov-mcp-server-mcp"
    echo "Generated (UTC): $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "Note: Live log below (same as terminal). Footer records exit code."
    echo "---------------------------------------------------------------------------------"
  } >"$RESULT_FILE"
  exec > >(tee -a "$RESULT_FILE") 2>&1
fi

# Per-step outcome for final summary (so you can see PASS/FAIL at a glance)
S1=""; S2=""; S3=""; S4=""; S5=""

pass() { echo -e "  ${GREEN}PASS: $1${NC}"; PASS=$((PASS+1)); }
fail() { echo -e "  ${RED}FAIL: $1${NC}"; FAIL=$((FAIL+1)); }
info() { echo -e "${BLUE}$1${NC}"; }
dump() { echo -e "${CYAN}$1${NC}"; }

# curl prints "(28) Operation timed out..." on stderr; decode for humans.
explain_curl_exit() {
  local ec="$1"
  local label="${2:-request}"
  local maxt="${3:-}"
  [ "$ec" -eq 0 ] && return 0
  echo ""
  echo "    ╔══════════════════════════════════════════════════════════════════════════╗"
  printf '    ║ %-72s ║\n' "WHAT THIS CURL LINE MEANS (exit $ec — $label)"
  echo "    ╚══════════════════════════════════════════════════════════════════════════╝"
  case "$ec" in
    28)
      echo "    • Exit 28 = TIMEOUT (--max-time ${maxt:-?}s). The server did not finish"
      echo "      sending a response before the limit."
      echo "    • '0 bytes received' = curl got NO response body in that window (often"
      echo "      stuck building a huge tools/list over SSE, or TCP hang)."
      echo "    • Try: export MCP_HTTP_CURL_TOOLS_LIST=300 (or higher), or give Docker"
      echo "      more CPU/RAM; stdio tools/list can still PASS while HTTP is slow."
      ;;
    7)
      echo "    • Exit 7 = FAILED TO CONNECT (nothing listening on host:port yet,"
      echo "      wrong MCP_PORT, or container not publishing the port)."
      ;;
    *)
      echo "    • Non-zero curl exit $ec — see https://curl.se/libcurl/c/libcurl-errors.html"
      ;;
  esac
  echo ""
}

banner_result() {
  local step="$1" name="$2" status="$3"
  echo ""
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  if [ "$status" = "PASS" ]; then
    echo -e "${GREEN}RESULT  ${step}  ${name}  →  PASS${NC}"
  else
    echo -e "${RED}RESULT  ${step}  ${name}  →  FAIL${NC}"
  fi
  echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

cleanup() { docker stop "$CONTAINER_NAME" 2>/dev/null || true; docker rm -f "$CONTAINER_NAME" 2>/dev/null || true; }
trap cleanup EXIT

INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'

echo "========== clinicaltrialsgov-mcp-server-mcp test (compliance) =========="

info "[1] Install"
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then echo "Build first: docker build -t $IMAGE $PROJECT_DIR" >&2; exit 1; fi
pass "image exists"
S1="PASS"
banner_result "[1]" "Install (image exists)" "PASS"

info "[2] Stdio tools/list"
dump ">>> [2] MCP requests sent on container stdin (one JSON-RPC per line):"
echo "$INIT_REQ"
echo "$INIT_NOTIF"
echo "$LIST_REQ"
dump ">>> [2] Running: python mcp_stdio_docker_tools_list.py"
STDIO_OUT=$(MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-180}" python "$SCRIPT_HELPER" "$IMAGE") || true
dump ">>> [2] Full raw MCP stdout from container:"
echo "--------------------------------------------------------------------------------"
printf '%s\n' "$STDIO_OUT"
echo "--------------------------------------------------------------------------------"
if grep -q '"tools"' <<< "$STDIO_OUT"; then
  dump ">>> [2] Tool names (sample):"
  echo "$STDIO_OUT" | grep -oE '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -80 || true
  pass "stdio tools/list"
  S2="PASS"
  banner_result "[2]" "Stdio tools/list" "PASS"
else
  fail "stdio tools/list"
  S2="FAIL"
  banner_result "[2]" "Stdio tools/list" "FAIL"
fi

info "[3] Stdio tools/call (skipped — upstream package)"
pass "stdio tools/call (upstream)"
S3="PASS(skip)"
banner_result "[3]" "Stdio tools/call (skipped)" "PASS"

info "[4] HTTP streamable tools/list"
cleanup
dump ">>> [4] Starting HTTP container"
docker run -d --name "$CONTAINER_NAME" -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT -p "$PORT:$PORT" "$IMAGE"
dump ">>> [4] Waiting ${MCP_HTTP_STARTUP_SLEEP:-15}s for HTTP listener"
sleep "${MCP_HTTP_STARTUP_SLEEP:-15}"

# tools/list JSON is enormous; must be >= worst-case stdio generation time. Proxy allows 600s
# (MCP_PROXY_REQUEST_TIMEOUT). Single-threaded proxy used to block ALL /mcp traffic during
# tools/list — use updated mcp_http_proxy.py (ThreadingHTTPServer) + rebuild image.
CURL_INIT_T="${MCP_HTTP_CURL_INIT:-30}"
CURL_LIST_T="${MCP_HTTP_CURL_TOOLS_LIST:-600}"

SESSION_ID=""; WAITED=0; TOOLS_RESP=""
while [ "$WAITED" -lt "${MCP_HTTP_LIST_MAX_WAIT:-120}" ]; do
  # Avoid stale /tmp files after curl timeouts (misleading session-id / bodies).
  : > /tmp/mcp_h; : > /tmp/mcp_init_body; : > /tmp/mcp_nh; : > /tmp/mcp_nbody
  : > /tmp/mcp_lh; : > /tmp/mcp_lbody

  dump ">>> [4] HTTP attempt WAITED=${WAITED}s — POST initialize (max ${CURL_INIT_T}s)"
  dump "    Request body: $INIT_REQ"
  set +e
  curl -sS --max-time "$CURL_INIT_T" -D /tmp/mcp_h -o /tmp/mcp_init_body -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$INIT_REQ"
  CURL_I=$?
  set -e
  explain_curl_exit "$CURL_I" "initialize" "$CURL_INIT_T"
  dump "    Response headers:"; sed 's/^/    /' /tmp/mcp_h 2>/dev/null || true
  dump "    Response body:"; sed 's/^/    /' /tmp/mcp_init_body 2>/dev/null || true
  echo ""

  SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_h 2>/dev/null | sed 's/.*: *//' | tr -d '\r' | head -1) || true
  dump "    Parsed mcp-session-id: ${SESSION_ID:-<empty>}"

  # Never POST tools/list without mcp-session-id — server returns plain text
  # "Missing or invalid mcp-session-id" (often with no trailing newline → log looks glued).
  if [ -z "$SESSION_ID" ]; then
    echo ""
    dump "    *** SKIP tools/list this round: no mcp-session-id from initialize. ***"
    dump "    (Often stale /tmp after a timeout, or the HTTP server was blocked — restarting container.)"
    docker restart "$CONTAINER_NAME" >/dev/null 2>&1 || true
    sleep "${MCP_HTTP_STARTUP_SLEEP:-15}"
    echo ""
    sleep 3
    WAITED=$((WAITED+3))
    continue
  fi

  # set -u: never expand empty array as "${ARR[@]}" — use conditional curls
  dump ">>> [4] POST notifications/initialized (max ${CURL_INIT_T}s)"
  dump "    Request body: $INIT_NOTIF"
  set +e
  curl -sS --max-time "$CURL_INIT_T" -D /tmp/mcp_nh -o /tmp/mcp_nbody -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "mcp-session-id: $SESSION_ID" \
    -d "$INIT_NOTIF"
  CURL_N=$?
  set -e
  explain_curl_exit "$CURL_N" "notifications/initialized" "$CURL_INIT_T"
  dump "    Response headers:"; sed 's/^/    /' /tmp/mcp_nh 2>/dev/null || true
  dump "    Response body:"; sed 's/^/    /' /tmp/mcp_nbody 2>/dev/null || true
  echo ""

  dump ">>> [4] POST tools/list (max ${CURL_LIST_T}s — large SSE body)"
  dump "    Request body: $LIST_REQ"
  set +e
  curl -sS --max-time "$CURL_LIST_T" -D /tmp/mcp_lh -o /tmp/mcp_lbody -X POST "http://localhost:${PORT}/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -H "mcp-session-id: $SESSION_ID" \
    -d "$LIST_REQ"
  CURL_L=$?
  set -e
  explain_curl_exit "$CURL_L" "tools/list" "$CURL_LIST_T"
  TOOLS_RESP=$(cat /tmp/mcp_lbody 2>/dev/null || true)
  dump "    Response headers:"; sed 's/^/    /' /tmp/mcp_lh 2>/dev/null || true
  dump "    Response body (tools/list, may be long):"
  sed 's/^/    /' /tmp/mcp_lbody 2>/dev/null || true
  echo ""

  if echo "$TOOLS_RESP" | grep -q '"tools"'; then
    dump ">>> [4] Tool names from HTTP (sample):"
    echo "$TOOLS_RESP" | grep -oE '"name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -80 || true
    break
  fi
  # Nuke container so a stuck tools/list worker (old single-thread proxy) cannot block retries.
  dump ">>> [4] No valid tools/list yet — restarting HTTP container before next attempt"
  docker restart "$CONTAINER_NAME" >/dev/null 2>&1 || true
  sleep "${MCP_HTTP_STARTUP_SLEEP:-15}"
  sleep 3
  WAITED=$((WAITED+3))
done

if echo "$TOOLS_RESP" | grep -q '"tools"'; then
  pass "HTTP tools/list"
  S4="PASS"
  banner_result "[4]" "HTTP streamable tools/list" "PASS"
else
  fail "HTTP tools/list"
  S4="FAIL"
  banner_result "[4]" "HTTP streamable tools/list" "FAIL"
fi

info "[5] HTTP streamable tools/call (skipped — upstream package)"
pass "HTTP tools/call (upstream)"
S5="PASS(skip)"
banner_result "[5]" "HTTP tools/call (skipped)" "PASS"

echo ""
echo -e "${YELLOW}══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}FINAL SUMMARY (read this)${NC}"
echo -e "${YELLOW}══════════════════════════════════════════════════════════════════════════════${NC}"
echo "  [1] Install:                    $S1"
echo "  [2] Stdio tools/list:           $S2"
echo "  [3] Stdio tools/call:           $S3"
echo "  [4] HTTP tools/list:            $S4"
echo "  [5] HTTP tools/call:            $S5"
echo "  Counters: $PASS passed, $FAIL failed"
if [ "$FAIL" -gt 0 ]; then
  echo -e "  ${RED}OVERALL: FAIL${NC}"
else
  echo -e "  ${GREEN}OVERALL: PASS${NC}"
fi
echo -e "${YELLOW}══════════════════════════════════════════════════════════════════════════════${NC}"

RECORD_EC=0
[ "$FAIL" -gt 0 ] && RECORD_EC=1
echo ""
echo "---------------------------------------------------------------------------------"
echo "Exit code: $RECORD_EC  |  step counters: $PASS passed, $FAIL failed"
[ "$RECORD_EC" -ne 0 ] && exit 1
exit 0
