#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @mcp-b/chrome-devtools-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8631} -- npx -y @mcp-b/chrome-devtools-mcp
fi
