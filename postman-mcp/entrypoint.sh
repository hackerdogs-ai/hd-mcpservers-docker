#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @postman/postman-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8658} -- npx -y @postman/postman-mcp-server
fi
