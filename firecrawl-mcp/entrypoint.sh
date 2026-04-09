#!/bin/sh
if command -v firecrawl-mcp >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec firecrawl-mcp
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8640}" -- firecrawl-mcp
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y firecrawl-mcp
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8640}" -- npx -y firecrawl-mcp
