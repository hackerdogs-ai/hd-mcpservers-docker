#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @tomtom-org/tomtom-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8671} -- npx -y @tomtom-org/tomtom-mcp
fi
