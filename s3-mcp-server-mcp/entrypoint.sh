#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @geunoh/s3-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8662} -- npx -y @geunoh/s3-mcp-server
fi
