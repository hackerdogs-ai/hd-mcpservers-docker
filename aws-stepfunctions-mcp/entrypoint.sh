#!/bin/sh
export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
export AWS_DEFAULT_PROFILE=
export FASTMCP_TRANSPORT=${MCP_TRANSPORT:-stdio}
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=${MCP_PORT:-8625}
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec python /app/mcp_server.py
else
  # Child must speak MCP over stdio to the proxy. Container still has
  # MCP_TRANSPORT=streamable-http from docker -e; if we don't override,
  # mcp_server.py starts FastMCP HTTP on the same port and initialize hangs.
  export FASTMCP_TRANSPORT=stdio
  exec python /mcp_http_proxy.py --port ${MCP_PORT:-8625} -- env MCP_TRANSPORT=stdio FASTMCP_TRANSPORT=stdio python /app/mcp_server.py
fi
