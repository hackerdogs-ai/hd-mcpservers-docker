#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @cenemiljezweb/dns-mcp-server
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8635} -- npx -y @cenemiljezweb/dns-mcp-server
fi
