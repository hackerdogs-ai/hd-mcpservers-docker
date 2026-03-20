#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @pinecone-database/mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8657} -- npx -y @pinecone-database/mcp
fi
