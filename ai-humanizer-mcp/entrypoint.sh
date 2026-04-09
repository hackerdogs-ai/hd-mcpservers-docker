#!/bin/sh
# Text2Go docs: npx -y ai-humanizer-mcp-server
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y ai-humanizer-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8601} -- npx -y ai-humanizer-mcp-server
fi
