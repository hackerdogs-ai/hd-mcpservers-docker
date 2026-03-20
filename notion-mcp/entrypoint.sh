#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @notionhq/notion-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8652} -- npx -y @notionhq/notion-mcp-server
fi
