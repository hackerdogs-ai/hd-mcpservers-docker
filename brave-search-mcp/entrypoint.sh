#!/bin/sh
# Prefer globally installed package (Dockerfile npm install -g) to avoid npx cold start.
if command -v mcp-server-brave-search >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec mcp-server-brave-search
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8629}" -- mcp-server-brave-search
else
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec npx -y @modelcontextprotocol/server-brave-search
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8629}" -- npx -y @modelcontextprotocol/server-brave-search
fi
