#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @zereight/mcp-gitlab
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8642} -- npx -y @zereight/mcp-gitlab
fi
