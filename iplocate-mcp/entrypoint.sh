#!/bin/sh
if command -v mcp-server-iplocate >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec mcp-server-iplocate
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8648}" -- mcp-server-iplocate
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @iplocate/mcp-server
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8648}" -- npx -y @iplocate/mcp-server
