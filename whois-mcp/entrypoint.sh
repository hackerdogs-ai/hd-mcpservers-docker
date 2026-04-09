#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y whois-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8673} -- npx -y whois-mcp
fi
