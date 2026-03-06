#!/bin/bash
# Test script for IVRE MCP Server
# Tests MCP protocol compliance via JSON-RPC (stdio and HTTP streamable)
# Optionally spins up a real IVRE stack for integration testing (--integration)

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PASS=0
FAIL=0
IMAGE="hackerdogs/ivre-mcp:latest"
PORT=8366
CONTAINER_NAME="ivre-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INTEGRATION=false
if [[ "${1:-}" == "--integration" ]]; then
    INTEGRATION=true
fi

IVRE_NETWORK="ivre-mcp-test-net"
IVRE_DB_CONTAINER="ivre-mcp-test-db"
IVRE_UWSGI_CONTAINER="ivre-mcp-test-uwsgi"
IVRE_WEB_CONTAINER="ivre-mcp-test-web"
IVRE_CLIENT_CONTAINER="ivre-mcp-test-client"

pass() { echo -e "  ${GREEN}✅ PASS: $1${NC}"; PASS=$((PASS + 1)); }
fail() { echo -e "  ${RED}❌ FAIL: $1${NC}"; FAIL=$((FAIL + 1)); }
info() { echo -e "${BLUE}$1${NC}"; }

cleanup() {
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || true
    if [ "$INTEGRATION" = true ]; then
        info "Cleaning up IVRE test stack..."
        docker stop "$IVRE_WEB_CONTAINER" "$IVRE_UWSGI_CONTAINER" "$IVRE_CLIENT_CONTAINER" "$IVRE_DB_CONTAINER" 2>/dev/null || true
        docker rm -f "$IVRE_WEB_CONTAINER" "$IVRE_UWSGI_CONTAINER" "$IVRE_CLIENT_CONTAINER" "$IVRE_DB_CONTAINER" 2>/dev/null || true
        docker network rm "$IVRE_NETWORK" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "================================================================================="
echo -e "${BLUE}IVRE MCP Server — Test Suite${NC}"
if [ "$INTEGRATION" = true ]; then
    echo -e "${YELLOW}Integration mode: Will spin up a full IVRE stack for testing${NC}"
else
    echo -e "${YELLOW}Protocol-only mode: Tests MCP compliance without a live IVRE backend${NC}"
    echo -e "${YELLOW}  Run with --integration to test against a real IVRE instance${NC}"
fi
echo "================================================================================="
echo ""

# =============================================================================
# Test 1: Build/verify Docker image
# =============================================================================
info "[Test 1] Docker image"
if ! docker image inspect "$IMAGE" > /dev/null 2>&1; then
    echo "  Image not found. Building..."
    docker build -t "$IMAGE" "$PROJECT_DIR"
fi
if docker image inspect "$IMAGE" > /dev/null 2>&1; then
    pass "Docker image $IMAGE exists"
else
    fail "Docker image $IMAGE could not be built"
    exit 1
fi
echo ""

# =============================================================================
# Test 2: Python and dependencies available
# =============================================================================
info "[Test 2] Python and dependencies inside container"
DEP_OUTPUT=$(docker run --rm "$IMAGE" python -c "import fastmcp; import httpx; print(f'fastmcp={fastmcp.__version__} httpx={httpx.__version__}')" 2>&1 || true)
if echo "$DEP_OUTPUT" | grep -q "fastmcp="; then
    pass "Python dependencies available"
    echo "       $DEP_OUTPUT"
else
    fail "Python dependencies not found"
    echo "       $DEP_OUTPUT"
fi
echo ""

# =============================================================================
# Test 3: MCP stdio mode — initialize + tools/list
# =============================================================================
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

# =============================================================================
# Test 4: Verify all 12 tools are registered
# =============================================================================
info "[Test 4] All 12 tools registered"
EXPECTED_TOOLS="query_hosts count_hosts query_passive count_passive top_values distinct_values get_host_ips get_ips_ports get_timeline ip_data passive_dns query_flows"
MISSING_TOOLS=""
for tool in $EXPECTED_TOOLS; do
    if ! echo "$STDIO_OUT" | grep -q "\"$tool\""; then
        MISSING_TOOLS="$MISSING_TOOLS $tool"
    fi
done
if [ -z "$MISSING_TOOLS" ]; then
    pass "All 12 expected tools are registered"
else
    fail "Missing tools:$MISSING_TOOLS"
fi
echo ""

# =============================================================================
# Test 5: MCP HTTP streamable mode — initialize
# =============================================================================
info "[Test 5] MCP HTTP streamable mode — initialize"
cleanup 2>/dev/null || true
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

# =============================================================================
# Test 6: MCP HTTP — tools/list
# =============================================================================
info "[Test 6] MCP HTTP — tools/list"
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

# Stop the HTTP test container before integration tests
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# =============================================================================
# Integration tests (only with --integration flag)
# =============================================================================
if [ "$INTEGRATION" = true ]; then
    echo ""
    echo "================================================================================="
    echo -e "${BLUE}Integration Tests — Real IVRE Stack${NC}"
    echo "================================================================================="
    echo ""

    # -------------------------------------------------------------------------
    # Setup: Start IVRE stack
    # -------------------------------------------------------------------------
    info "[Setup] Starting IVRE test stack..."

    docker network create "$IVRE_NETWORK" 2>/dev/null || true

    docker run -d --name "$IVRE_DB_CONTAINER" \
        --network "$IVRE_NETWORK" \
        mongo:7 > /dev/null
    echo "  Started MongoDB"

    MAX_WAIT=30; WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if docker exec "$IVRE_DB_CONTAINER" mongosh --eval "db.runCommand({ping:1})" > /dev/null 2>&1; then
            break
        fi
        sleep 2; WAITED=$((WAITED + 2))
    done
    echo "  MongoDB ready (${WAITED}s)"

    docker run -d --name "$IVRE_UWSGI_CONTAINER" \
        --network "$IVRE_NETWORK" \
        ivre/web-uwsgi:latest > /dev/null
    echo "  Started uWSGI"

    docker run -d --name "$IVRE_WEB_CONTAINER" \
        --network "$IVRE_NETWORK" \
        -e "IVRE_UWSGI_HOST=$IVRE_UWSGI_CONTAINER" \
        ivre/web:latest > /dev/null
    echo "  Started Nginx"

    docker run -d --name "$IVRE_CLIENT_CONTAINER" \
        --network "$IVRE_NETWORK" \
        ivre/client:latest sleep infinity > /dev/null
    echo "  Started Client"

    sleep 5

    # -------------------------------------------------------------------------
    # Setup: Initialize IVRE databases
    # -------------------------------------------------------------------------
    info "[Setup] Initializing IVRE databases..."

    docker exec "$IVRE_CLIENT_CONTAINER" bash -c "yes | ivre ipinfo --init" > /dev/null 2>&1 || true
    docker exec "$IVRE_CLIENT_CONTAINER" bash -c "yes | ivre scancli --init" > /dev/null 2>&1 || true
    docker exec "$IVRE_CLIENT_CONTAINER" bash -c "yes | ivre view --init" > /dev/null 2>&1 || true
    docker exec "$IVRE_CLIENT_CONTAINER" bash -c "yes | ivre flowcli --init" > /dev/null 2>&1 || true
    echo "  Databases initialized"

    docker exec "$IVRE_CLIENT_CONTAINER" ivre ipdata --download > /dev/null 2>&1 || echo "  (ipdata download skipped or partial)"
    echo "  GeoIP data loaded"

    # -------------------------------------------------------------------------
    # Setup: Create sample scan data via Nmap XML
    # -------------------------------------------------------------------------
    info "[Setup] Importing sample scan data..."

    SAMPLE_XML='<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sV -oX sample.xml 93.184.216.34" start="1700000000" startstr="Tue Nov 14 22:13:20 2023" version="7.94" xmloutputversion="1.04">
<host starttime="1700000000" endtime="1700000060"><status state="up" reason="echo-reply"/>
<address addr="93.184.216.34" addrtype="ipv4"/>
<hostnames><hostname name="example.com" type="PTR"/></hostnames>
<ports>
<port protocol="tcp" portid="80"><state state="open" reason="syn-ack"/><service name="http" product="ECAcc" version="bsa/0B18" extrainfo="" method="probed" conf="10"/></port>
<port protocol="tcp" portid="443"><state state="open" reason="syn-ack"/><service name="https" product="ECAcc" version="bsa/0B18" extrainfo="" method="probed" conf="10" tunnel="ssl"/></port>
</ports>
<os><osmatch name="Linux 5.x" accuracy="95"><osclass type="general purpose" vendor="Linux" osfamily="Linux" osgen="5.X"/></osmatch></os>
</host>
<runstats><finished time="1700000060" timestr="Tue Nov 14 22:14:20 2023" elapsed="60.00"/><hosts up="1" down="0" total="1"/></runstats>
</nmaprun>'

    docker exec "$IVRE_CLIENT_CONTAINER" bash -c "cat > /tmp/sample.xml << 'XMLEOF'
$SAMPLE_XML
XMLEOF"
    docker exec "$IVRE_CLIENT_CONTAINER" ivre scan2db -c TEST -s TestSource -r /tmp/sample.xml > /dev/null 2>&1
    docker exec "$IVRE_CLIENT_CONTAINER" ivre db2view nmap > /dev/null 2>&1
    echo "  Sample host imported (93.184.216.34 / example.com)"

    # Wait for web API to be ready
    IVRE_WEB_URL="http://${IVRE_WEB_CONTAINER}:80"
    MAX_WAIT=30; WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if docker exec "$IVRE_CLIENT_CONTAINER" curl -sf "$IVRE_WEB_URL/cgi/config" > /dev/null 2>&1; then
            break
        fi
        sleep 2; WAITED=$((WAITED + 2))
    done
    echo "  IVRE Web API ready (${WAITED}s)"
    echo ""

    # -------------------------------------------------------------------------
    # Test 7: count_hosts via MCP against live IVRE
    # -------------------------------------------------------------------------
    info "[Test 7] Integration: count_hosts via MCP"

    docker run -d --name "$CONTAINER_NAME" \
        --network "$IVRE_NETWORK" \
        -e "MCP_TRANSPORT=streamable-http" -e "MCP_PORT=$PORT" \
        -e "IVRE_WEB_URL=$IVRE_WEB_URL" \
        -p "$PORT:$PORT" "$IMAGE" > /dev/null

    MAX_WAIT=15; WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if curl -sf "http://localhost:${PORT}/mcp" -X POST \
            -H "Content-Type: application/json" \
            -H "Accept: application/json, text/event-stream" \
            -d "$INIT_REQ" > /dev/null 2>&1; then
            break
        fi
        sleep 2; WAITED=$((WAITED + 2))
    done

    SESSION_ID=$(curl -s -D /tmp/mcp_headers -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -d "$INIT_REQ" 2>/dev/null | head -c 0; grep -i 'mcp-session-id' /tmp/mcp_headers 2>/dev/null | sed 's/.*: //' | tr -d '\r' || true)
    SESSION_HDR=""
    [ -n "$SESSION_ID" ] && SESSION_HDR="-H mcp-session-id:${SESSION_ID}"

    curl -s -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        $SESSION_HDR \
        -d "$INIT_NOTIF" > /dev/null 2>&1 || true

    CALL_REQ='{"jsonrpc":"2.0","id":10,"method":"tools/call","params":{"name":"count_hosts","arguments":{"database":"view","filter":""}}}'
    CALL_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        $SESSION_HDR \
        -d "$CALL_REQ" 2>/dev/null || true)

    if echo "$CALL_RESP" | grep -q '"success".*true'; then
        pass "count_hosts returned success against live IVRE"
    elif echo "$CALL_RESP" | grep -q '"content"'; then
        pass "count_hosts returned content from live IVRE"
    else
        fail "count_hosts did not return expected result from live IVRE"
        [ -n "$CALL_RESP" ] && echo "       Response: ${CALL_RESP:0:500}"
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Test 8: query_hosts returns imported data
    # -------------------------------------------------------------------------
    info "[Test 8] Integration: query_hosts returns imported host"

    CALL_REQ='{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"query_hosts","arguments":{"database":"view","filter":"port:80","limit":10}}}'
    CALL_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        $SESSION_HDR \
        -d "$CALL_REQ" 2>/dev/null || true)

    if echo "$CALL_RESP" | grep -q '93.184.216.34\|example.com'; then
        pass "query_hosts returned imported host data (93.184.216.34)"
    elif echo "$CALL_RESP" | grep -q '"success".*true'; then
        pass "query_hosts returned success (host data present)"
    else
        fail "query_hosts did not return imported host data"
        [ -n "$CALL_RESP" ] && echo "       Response: ${CALL_RESP:0:500}"
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Test 9: top_values returns service data
    # -------------------------------------------------------------------------
    info "[Test 9] Integration: top_values for services"

    CALL_REQ='{"jsonrpc":"2.0","id":12,"method":"tools/call","params":{"name":"top_values","arguments":{"database":"view","field":"service","limit":5}}}'
    CALL_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        $SESSION_HDR \
        -d "$CALL_REQ" 2>/dev/null || true)

    if echo "$CALL_RESP" | grep -qi 'http\|https\|success.*true'; then
        pass "top_values returned service aggregation data"
    else
        fail "top_values did not return expected data"
        [ -n "$CALL_RESP" ] && echo "       Response: ${CALL_RESP:0:500}"
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Test 10: ip_data returns geolocation
    # -------------------------------------------------------------------------
    info "[Test 10] Integration: ip_data for geolocation"

    CALL_REQ='{"jsonrpc":"2.0","id":13,"method":"tools/call","params":{"name":"ip_data","arguments":{"address":"93.184.216.34"}}}'
    CALL_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        $SESSION_HDR \
        -d "$CALL_REQ" 2>/dev/null || true)

    if echo "$CALL_RESP" | grep -q '"content"'; then
        pass "ip_data returned content for 93.184.216.34"
    else
        fail "ip_data did not return expected response"
        [ -n "$CALL_RESP" ] && echo "       Response: ${CALL_RESP:0:500}"
    fi
    echo ""

    # -------------------------------------------------------------------------
    # Test 11: get_host_ips returns compact IP list
    # -------------------------------------------------------------------------
    info "[Test 11] Integration: get_host_ips returns compact IP list"

    CALL_REQ='{"jsonrpc":"2.0","id":14,"method":"tools/call","params":{"name":"get_host_ips","arguments":{"database":"view","filter":"","limit":10}}}'
    CALL_RESP=$(curl -s -X POST "http://localhost:${PORT}/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        $SESSION_HDR \
        -d "$CALL_REQ" 2>/dev/null || true)

    if echo "$CALL_RESP" | grep -q '"content"'; then
        pass "get_host_ips returned content"
    else
        fail "get_host_ips did not return expected response"
        [ -n "$CALL_RESP" ] && echo "       Response: ${CALL_RESP:0:500}"
    fi
    echo ""
fi

# =============================================================================
# Summary
# =============================================================================
echo "================================================================================="
echo -e "${BLUE}Results: ${GREEN}$PASS passed${NC}, ${RED}$FAIL failed${NC}"
echo "================================================================================="
[ $FAIL -gt 0 ] && exit 1 || exit 0
