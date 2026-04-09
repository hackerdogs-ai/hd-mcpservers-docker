#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @upstash/context7-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8634} -- npx -y @upstash/context7-mcp
fi
