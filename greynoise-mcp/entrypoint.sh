#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @greynoise/greynoise-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8645} -- npx -y @greynoise/greynoise-mcp-server
fi
