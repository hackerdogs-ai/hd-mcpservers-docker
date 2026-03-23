#!/bin/sh
if command -v mcp-dnstwist >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec mcp-dnstwist
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8636}" -- mcp-dnstwist
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @burtthecoder/mcp-dnstwist
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8636}" -- npx -y @burtthecoder/mcp-dnstwist
