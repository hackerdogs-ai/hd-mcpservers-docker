#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @cloudflare/mcp-server-cloudflare run "${CLOUDFLARE_ACCOUNT_ID:-PLACEHOLDER}"
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8633} -- npx -y @cloudflare/mcp-server-cloudflare run "${CLOUDFLARE_ACCOUNT_ID:-PLACEHOLDER}"
fi
