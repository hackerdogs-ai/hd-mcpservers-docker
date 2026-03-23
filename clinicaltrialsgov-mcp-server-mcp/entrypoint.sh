#!/bin/sh
if command -v clinicaltrialsgov-mcp-server >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec clinicaltrialsgov-mcp-server
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8632}" -- clinicaltrialsgov-mcp-server
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y clinicaltrialsgov-mcp-server
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8632}" -- npx -y clinicaltrialsgov-mcp-server
