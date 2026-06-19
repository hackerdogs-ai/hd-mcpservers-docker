#!/bin/sh
if command -v clinicaltrialsgov-mcp-server >/dev/null 2>&1; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec clinicaltrialsgov-mcp-server
  fi
  # Wrapped MCP must use stdio toward the proxy; outer MCP_TRANSPORT is streamable-http.
  MCP_TRANSPORT=stdio exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8632}" -- clinicaltrialsgov-mcp-server
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y clinicaltrialsgov-mcp-server
fi
MCP_TRANSPORT=stdio exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8632}" -- npx -y clinicaltrialsgov-mcp-server
