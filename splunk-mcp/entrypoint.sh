#!/bin/sh
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec npx -y splunk-mcp
else
  exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8667} -- npx -y splunk-mcp
fi
