#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @darrenjrobinson/hibp-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8646} -- npx -y @darrenjrobinson/hibp-mcp
fi
