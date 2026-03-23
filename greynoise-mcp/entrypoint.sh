#!/bin/sh
if command -v gnapi >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec gnapi
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8645}" -- gnapi
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @greynoise/greynoise-mcp-server
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8645}" -- npx -y @greynoise/greynoise-mcp-server
