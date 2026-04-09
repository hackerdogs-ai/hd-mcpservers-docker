#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @globalping/globalping-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8643} -- npx -y @globalping/globalping-mcp
fi
