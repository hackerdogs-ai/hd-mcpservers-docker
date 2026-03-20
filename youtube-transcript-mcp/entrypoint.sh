#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @kimtaeyoon83/mcp-server-youtube-transcript
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8675} -- npx -y @kimtaeyoon83/mcp-server-youtube-transcript
fi
