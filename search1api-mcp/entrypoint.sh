#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y search1api-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8664} -- npx -y search1api-mcp
fi
