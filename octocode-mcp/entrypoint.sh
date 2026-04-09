#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y octocode-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8654} -- npx -y octocode-mcp
fi
