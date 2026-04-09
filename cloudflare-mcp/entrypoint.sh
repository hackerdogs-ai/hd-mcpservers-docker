#!/bin/sh
CF_ACCOUNT="${CLOUDFLARE_ACCOUNT_ID:-00000000000000000000000000000000}"
if command -v mcp-server-cloudflare >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec mcp-server-cloudflare run "$CF_ACCOUNT"
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8633}" -- mcp-server-cloudflare run "$CF_ACCOUNT"
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @cloudflare/mcp-server-cloudflare run "$CF_ACCOUNT"
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8633}" -- npx -y @cloudflare/mcp-server-cloudflare run "$CF_ACCOUNT"
