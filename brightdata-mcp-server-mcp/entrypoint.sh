#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @brightdata/mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8630} -- npx -y @brightdata/mcp
fi
