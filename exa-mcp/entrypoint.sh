#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec node /usr/local/lib/node_modules/exa-mcp-server/.smithery/stdio/index.cjs
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8637} -- node /usr/local/lib/node_modules/exa-mcp-server/.smithery/stdio/index.cjs
fi
