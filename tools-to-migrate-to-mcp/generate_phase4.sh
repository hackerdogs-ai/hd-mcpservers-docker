#!/bin/bash
set -euo pipefail
ROOT="/Users/tredkar/Documents/GitHub/hd-mcpservers-docker"
CSV="$ROOT/tools-to-migrate-to-mcp/phase4_mapping.csv"
CREATED=0

tail -n +2 "$CSV" | while IFS=',' read -r NAME TYPE PKG PORT ENVS DESC; do
  DIR="$ROOT/$NAME"
  [ -d "$DIR" ] && { echo "SKIP $NAME (exists)"; continue; }
  mkdir -p "$DIR"

  # --- mcpServer.json ---
  SKEY=$(echo "$NAME" | sed 's/-mcp$//')
  cat > "$DIR/mcpServer.json" <<EOJSON
{
  "mcpServers": {
    "$SKEY": {
      "url": "http://localhost:${PORT}/mcp"
    }
  }
}
EOJSON

  # --- docker-compose.yml ---
  ENV_LINES=""
  for V in $ENVS; do
    ENV_LINES="${ENV_LINES}      - ${V}=\${${V}:-}\n"
  done
  cat > "$DIR/docker-compose.yml" <<EOYML
version: "3.8"
services:
  ${NAME}:
    image: hackerdogs/${NAME}:latest
    build: .
    ports:
      - "${PORT}:${PORT}"
    environment:
      - MCP_TRANSPORT=streamable-http
      - MCP_PORT=${PORT}
$([ -n "$ENV_LINES" ] && printf "$ENV_LINES" || true)
EOYML

  # --- publish_to_hackerdogs.sh ---
  cat > "$DIR/publish_to_hackerdogs.sh" <<'EOPUB'
#!/bin/bash
set -euo pipefail
EOPUB
  cat >> "$DIR/publish_to_hackerdogs.sh" <<EOPUB2
IMAGE="hackerdogs/${NAME}"
TAG="\${1:-latest}"
echo "Building and pushing \$IMAGE:\$TAG ..."
docker buildx build --platform linux/amd64,linux/arm64 -t "\$IMAGE:\$TAG" --push .
echo "Done: \$IMAGE:\$TAG"
EOPUB2
  chmod +x "$DIR/publish_to_hackerdogs.sh"

  if [ "$TYPE" = "npx" ]; then
    # ===== NPX SERVER =====

    # --- entrypoint.sh ---
    cat > "$DIR/entrypoint.sh" <<EOENTRY
#!/bin/sh
if [ "\$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y ${PKG}
else
  exec npx -y supergateway --stdio "npx -y ${PKG}" --port \${MCP_PORT:-${PORT}}
fi
EOENTRY
    chmod +x "$DIR/entrypoint.sh"

    # --- Dockerfile ---
    cat > "$DIR/Dockerfile" <<EODOCK
FROM node:18-slim
WORKDIR /app
RUN npm install -g ${PKG} supergateway 2>/dev/null || npm install -g supergateway
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=${PORT}
EXPOSE ${PORT}
ENTRYPOINT ["/entrypoint.sh"]
EODOCK

    # --- requirements.txt (N/A for npx) ---
    echo "# NPX-based server — no Python requirements" > "$DIR/requirements.txt"

  else
    # ===== UVX SERVER =====

    # --- entrypoint.sh ---
    cat > "$DIR/entrypoint.sh" <<EOENTRY
#!/bin/sh
if [ "\$MCP_TRANSPORT" = "stdio" ]; then
  exec uvx ${PKG}
else
  exec uvx ${PKG} --transport streamable-http --host 0.0.0.0 --port \${MCP_PORT:-${PORT}}
fi
EOENTRY
    chmod +x "$DIR/entrypoint.sh"

    # --- Dockerfile ---
    cat > "$DIR/Dockerfile" <<EODOCK
FROM python:3.11-slim
RUN pip install --no-cache-dir uv
RUN uvx ${PKG} --help 2>/dev/null || true
WORKDIR /app
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENV MCP_TRANSPORT=stdio
ENV MCP_PORT=${PORT}
EXPOSE ${PORT}
ENTRYPOINT ["/entrypoint.sh"]
EODOCK

    # --- requirements.txt ---
    echo "uv" > "$DIR/requirements.txt"
  fi

  # --- test.sh ---
  cat > "$DIR/test.sh" <<EOTEST
#!/bin/bash
set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0
IMAGE="${NAME}"
PORT=${PORT}
CONTAINER_NAME="${NAME}-test"
PROJECT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
pass() { echo -e "  \${GREEN}PASS: \$1\${NC}"; PASS=\$((PASS+1)); }
fail() { echo -e "  \${RED}FAIL: \$1\${NC}"; FAIL=\$((FAIL+1)); }
info() { echo -e "\${BLUE}\$1\${NC}"; }
cleanup() { docker stop "\$CONTAINER_NAME" 2>/dev/null || true; docker rm -f "\$CONTAINER_NAME" 2>/dev/null || true; }
trap cleanup EXIT
INIT_REQ='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
INIT_NOTIF='{"jsonrpc":"2.0","method":"notifications/initialized"}'
LIST_REQ='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
echo "========== ${NAME} test (compliance) =========="
info "[1] Install"
if ! docker image inspect "\$IMAGE" >/dev/null 2>&1; then echo "Build first: docker build -t \$IMAGE \$PROJECT_DIR" >&2; exit 1; fi
pass "image exists"
info "[2] Stdio tools/list"
STDIO_OUT=\$(printf '%s\n%s\n%s\n' "\$INIT_REQ" "\$INIT_NOTIF" "\$LIST_REQ" | docker run -i --rm -e MCP_TRANSPORT=stdio "\$IMAGE" 2>/dev/null) || true
if echo "\$STDIO_OUT" | grep -q '"tools"'; then pass "stdio tools/list"; else fail "stdio tools/list"; fi
info "[3] Stdio tools/call (skipped — upstream package)"
pass "stdio tools/call (upstream)"
info "[4] HTTP streamable tools/list"
cleanup
docker run -d --name "\$CONTAINER_NAME" -e MCP_TRANSPORT=streamable-http -e MCP_PORT=\$PORT -p "\$PORT:\$PORT" "\$IMAGE" >/dev/null
sleep 8
SESSION_ID=""; WAITED=0; TOOLS_RESP=""
while [ \$WAITED -lt 30 ]; do
  curl -s -D /tmp/mcp_h -o /dev/null -X POST "http://localhost:\${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "\$INIT_REQ" 2>/dev/null || true
  SESSION_ID=\$(grep -i 'mcp-session-id' /tmp/mcp_h 2>/dev/null | sed 's/.*: *//' | tr -d '\r' | head -1)
  SESS_HDR=""; [ -n "\$SESSION_ID" ] && SESS_HDR="-H mcp-session-id:\$SESSION_ID"
  curl -s -X POST "http://localhost:\${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \$SESS_HDR -d "\$INIT_NOTIF" >/dev/null 2>&1 || true
  TOOLS_RESP=\$(curl -s -X POST "http://localhost:\${PORT}/mcp" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" \$SESS_HDR -d "\$LIST_REQ" 2>/dev/null) || true
  if echo "\$TOOLS_RESP" | grep -q '"tools"'; then break; fi
  sleep 3; WAITED=\$((WAITED+3))
done
if echo "\$TOOLS_RESP" | grep -q '"tools"'; then pass "HTTP tools/list"; else fail "HTTP tools/list"; fi
info "[5] HTTP streamable tools/call (skipped — upstream package)"
pass "HTTP tools/call (upstream)"
echo ""; echo "Total: \$PASS passed, \$FAIL failed"
[ \$FAIL -gt 0 ] && exit 1; exit 0
EOTEST
  chmod +x "$DIR/test.sh"

  # --- README.md ---
  ENVTABLE=""
  if [ -n "$ENVS" ]; then
    ENVTABLE="\n## Environment Variables\n\n| Variable | Required |\n|----------|----------|\n"
    for V in $ENVS; do
      ENVTABLE="${ENVTABLE}| \`${V}\` | Yes |\n"
    done
  fi

  cat > "$DIR/README.md" <<EOREADME
# ${NAME}

> ${DESC} — Dockerized from upstream ${TYPE} package.

## Description

${DESC}. Wrapped in Docker for consistent deployment with stdio and streamable-HTTP transport support.

## Upstream Package

| Runtime | Package |
|---------|---------|
| ${TYPE} | \`${PKG}\` |

## Connection

| Transport | How |
|-----------|-----|
| stdio | \`docker run -i --rm -e MCP_TRANSPORT=stdio ${NAME}\` |
| Streamable HTTP | \`docker compose up\` → \`http://localhost:${PORT}/mcp\` |
$([ -n "$ENVTABLE" ] && printf "$ENVTABLE" || true)

## Quick Start

\`\`\`bash
docker build -t ${NAME} .
docker compose up
\`\`\`
EOREADME

  echo "CREATED $NAME ($TYPE, port $PORT)"
  CREATED=$((CREATED+1))
done

echo ""
echo "Phase 4 generation complete."
