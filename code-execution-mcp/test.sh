#!/bin/bash
set -euo pipefail
IMAGE="hackerdogs/code-execution-mcp:latest"
PORT=8376
CONTAINER_NAME="code-execution-mcp-test"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cleanup() { docker stop "$CONTAINER_NAME" 2>/dev/null || true; docker rm -f "$CONTAINER_NAME" 2>/dev/null || true; }
trap cleanup EXIT
docker build -t "$IMAGE" "$PROJECT_DIR" 2>/dev/null || true
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
STDIO_OUT=$(printf '%s\n%s\n%s\n' "$INIT_REQ" '{"jsonrpc":"2.0","method":"notifications/initialized"}' '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | docker run -i --rm -e MCP_TRANSPORT=stdio "$IMAGE" 2>/dev/null) || true
echo "$STDIO_OUT" | grep -q '"tools"' && echo "PASS stdio" || echo "FAIL stdio"
cleanup
docker run -d --name "$CONTAINER_NAME" -e MCP_TRANSPORT=streamable-http -e MCP_PORT=$PORT -p "$PORT:$PORT" "$IMAGE" >/dev/null
sleep 5
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "http://localhost:${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$INIT_REQ" 2>/dev/null) || CODE=000
[ "$CODE" = "200" ] || [ "$CODE" = "202" ] && echo "PASS HTTP $CODE" || echo "FAIL HTTP $CODE"
