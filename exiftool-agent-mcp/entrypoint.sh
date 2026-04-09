#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y exiftool-mcp-ai-agent
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8638} -- npx -y exiftool-mcp-ai-agent
fi
