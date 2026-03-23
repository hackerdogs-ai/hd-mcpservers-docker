#!/bin/sh
if command -v hibp-mcp >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec hibp-mcp
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8646}" -- hibp-mcp
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @darrenjrobinson/hibp-mcp
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8646}" -- npx -y @darrenjrobinson/hibp-mcp
