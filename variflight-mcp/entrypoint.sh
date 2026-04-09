#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y @variflight-ai/variflight-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8672} -- npx -y @variflight-ai/variflight-mcp
fi
