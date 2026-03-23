#!/bin/sh
if command -v nasa-mcp-server >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec nasa-mcp-server
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8651}" -- nasa-mcp-server
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @programcomputer/nasa-mcp-server
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8651}" -- npx -y @programcomputer/nasa-mcp-server
