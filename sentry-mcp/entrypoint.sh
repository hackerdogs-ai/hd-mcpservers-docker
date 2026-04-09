#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @sentry/mcp-server --access-token="${SENTRY_AUTH_TOKEN:-PLACEHOLDER}"
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8665} -- npx -y @sentry/mcp-server --access-token="${SENTRY_AUTH_TOKEN:-PLACEHOLDER}"
fi
