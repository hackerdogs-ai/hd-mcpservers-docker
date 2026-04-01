#!/bin/bash

# Usage: ./debug_test.sh <mcp-server-directory>
# Manually reproduces the failing stdio and HTTP tools/list checks
# with full raw output for debugging.

if [ -z "$1" ]; then
    echo "Usage: $0 <mcp-server-directory>"
    exit 1
fi

TARGET_DIR="${1%/}"
server_name=$(basename "$TARGET_DIR")
LOG_FILE="$TARGET_DIR/debug_verbose.txt"
CONTAINER_NAME="${server_name}-debug"
HTTP_PORT=8614

echo "========== VERBOSE DEBUG: $server_name ==========" | tee "$LOG_FILE"
echo "Timestamp: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# -------------------------------------------------------
# CHECK 1: Build the Docker image
# -------------------------------------------------------
echo "--- [CHECK 1] Building Docker image ---" | tee -a "$LOG_FILE"
echo ">>> docker build -t $server_name -t hackerdogs/$server_name:latest $TARGET_DIR" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if docker build -t "$server_name" -t "hackerdogs/$server_name:latest" "$TARGET_DIR" 2>&1 | tee -a "$LOG_FILE"; then
    echo "" | tee -a "$LOG_FILE"
    echo "✅ Build succeeded." | tee -a "$LOG_FILE"
else
    echo "" | tee -a "$LOG_FILE"
    echo "❌ Build FAILED — cannot proceed with tests." | tee -a "$LOG_FILE"
    exit 1
fi
echo "" | tee -a "$LOG_FILE"

# -------------------------------------------------------
# CHECK 2: Stdio tools/list  (the failing test)
# Sends a JSON-RPC initialize + tools/list over stdio
# -------------------------------------------------------
echo "--- [CHECK 2] Stdio tools/list (raw output) ---" | tee -a "$LOG_FILE"

STDIO_PAYLOAD=$(cat <<'EOF'
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"debug","version":"0.0.1"}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
EOF
)

echo ">>> Sending to container via stdio:" | tee -a "$LOG_FILE"
echo "$STDIO_PAYLOAD" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo ">>> Raw container response:" | tee -a "$LOG_FILE"

STDIO_RESPONSE=$(echo "$STDIO_PAYLOAD" | \
    docker run --rm -i \
        --name "${CONTAINER_NAME}-stdio" \
        -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-dummy}" \
        -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-dummy}" \
        -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}" \
        "$server_name" 2>&1)

echo "$STDIO_RESPONSE" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check if tools/list response is present
if echo "$STDIO_RESPONSE" | grep -q '"tools"'; then
    echo "✅ Stdio tools/list: tools key found in response." | tee -a "$LOG_FILE"
else
    echo "❌ Stdio tools/list: NO 'tools' key in response — see raw output above." | tee -a "$LOG_FILE"
fi
echo "" | tee -a "$LOG_FILE"

# -------------------------------------------------------
# CHECK 3: HTTP streamable tools/list  (the failing test)
# Starts container in HTTP mode, waits, hits /mcp initialize, then tools/list
# -------------------------------------------------------
echo "--- [CHECK 3] HTTP streamable tools/list (raw output) ---" | tee -a "$LOG_FILE"

# Clean up any leftover container
docker rm -f "${CONTAINER_NAME}-http" > /dev/null 2>&1

echo ">>> Starting container in HTTP mode on port $HTTP_PORT..." | tee -a "$LOG_FILE"
docker run -d \
    --name "${CONTAINER_NAME}-http" \
    -p "$HTTP_PORT:8800" \
    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID:-dummy}" \
    -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY:-dummy}" \
    -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-1}" \
    -e MCP_TRANSPORT=http \
    "$server_name" >> "$LOG_FILE" 2>&1

echo ">>> Waiting 5s for server to start..." | tee -a "$LOG_FILE"
sleep 5

echo ">>> Container logs so far:" | tee -a "$LOG_FILE"
docker logs "${CONTAINER_NAME}-http" 2>&1 | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

echo ">>> Sending HTTP initialize request to get session ID..." | tee -a "$LOG_FILE"
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"debug","version":"0.0.1"}}}'

curl -sv -D /tmp/mcp_headers.txt -X POST "http://localhost:$HTTP_PORT/mcp" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$INIT_REQ" >> "$LOG_FILE" 2>&1

SESSION_ID=$(grep -i 'mcp-session-id' /tmp/mcp_headers.txt | sed 's/.*: *//' | tr -d '\r' | head -1)

if [ -n "$SESSION_ID" ]; then
    echo "✅ Got session ID: $SESSION_ID" | tee -a "$LOG_FILE"
    
    echo ">>> Sending HTTP notifications/initialized..." | tee -a "$LOG_FILE"
    INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
    curl -sv -X POST "http://localhost:$HTTP_PORT/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -H "mcp-session-id: $SESSION_ID" \
        -d "$INIT_NOTIF" >> "$LOG_FILE" 2>&1

    echo ">>> Sending HTTP tools/list request:" | tee -a "$LOG_FILE"
    HTTP_PAYLOAD='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
    
    echo ">>> Raw HTTP response:" | tee -a "$LOG_FILE"
    HTTP_RESPONSE=$(curl -sv \
        -X POST "http://localhost:$HTTP_PORT/mcp" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json, text/event-stream" \
        -H "mcp-session-id: $SESSION_ID" \
        -d "$HTTP_PAYLOAD" \
        --max-time 30 2>&1)

    echo "$HTTP_RESPONSE" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"

    if echo "$HTTP_RESPONSE" | grep -q '"tools"'; then
        echo "✅ HTTP tools/list: tools key found in response." | tee -a "$LOG_FILE"
    else
        echo "❌ HTTP tools/list: NO 'tools' key — see raw output above." | tee -a "$LOG_FILE"
    fi
else
    echo "❌ HTTP tools/list: Failed to extract mcp-session-id. Raw headers:" | tee -a "$LOG_FILE"
    cat /tmp/mcp_headers.txt | tee -a "$LOG_FILE"
fi

# -------------------------------------------------------
# Cleanup
# -------------------------------------------------------
echo "" | tee -a "$LOG_FILE"
echo ">>> Stopping HTTP container..." | tee -a "$LOG_FILE"
docker rm -f "${CONTAINER_NAME}-http" >> "$LOG_FILE" 2>&1

echo "" | tee -a "$LOG_FILE"
echo "========== End of Debug: $(date) ==========" | tee -a "$LOG_FILE"
echo ""
echo "Full verbose log saved to: $LOG_FILE"