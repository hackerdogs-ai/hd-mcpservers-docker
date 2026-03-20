#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @modelcontextprotocol/server-puppeteer
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8659} -- npx -y @modelcontextprotocol/server-puppeteer
fi
