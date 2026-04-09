#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y serper-search-scrape-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8666} -- npx -y serper-search-scrape-mcp-server
fi
