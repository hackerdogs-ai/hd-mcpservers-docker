#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y clinicaltrialsgov-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8632} -- npx -y clinicaltrialsgov-mcp-server
fi
