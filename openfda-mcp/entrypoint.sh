#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @ythalorossy/openfda
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8655} -- npx -y @ythalorossy/openfda
fi
