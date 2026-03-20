#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @iplocate/mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8648} -- npx -y @iplocate/mcp-server
fi
