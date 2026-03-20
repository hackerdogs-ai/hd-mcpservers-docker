#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y firecrawl-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8640} -- npx -y firecrawl-mcp
fi
