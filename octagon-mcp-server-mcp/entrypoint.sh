#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y octagon-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8653} -- npx -y octagon-mcp
fi
