#!/bin/sh
# @brightdata/mcp exposes bin name "mcp" — use explicit server path when present.
BD_MAIN="/usr/local/lib/node_modules/@brightdata/mcp/server.js"
if [ -f "$BD_MAIN" ]; then
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec node "$BD_MAIN"
  fi
  exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8630}" -- node "$BD_MAIN"
fi
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @brightdata/mcp
fi
exec python3 /mcp_http_proxy.py --port "${MCP_PORT:-8630}" -- npx -y @brightdata/mcp
