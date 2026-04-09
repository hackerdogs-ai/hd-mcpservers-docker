#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y winston-ai-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8674} -- npx -y winston-ai-mcp
fi
