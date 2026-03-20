#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @programcomputer/nasa-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8651} -- npx -y @programcomputer/nasa-mcp-server
fi
