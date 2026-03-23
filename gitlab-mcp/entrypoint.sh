#!/bin/sh
if command -v mcp-gitlab >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec mcp-gitlab
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8642}" -- mcp-gitlab
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @zereight/mcp-gitlab
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8642}" -- npx -y @zereight/mcp-gitlab
