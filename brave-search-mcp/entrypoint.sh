#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @modelcontextprotocol/server-brave-search
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8629} -- npx -y @modelcontextprotocol/server-brave-search
fi
