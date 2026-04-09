#!/bin/sh
export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
export AWS_DEFAULT_PROFILE=
export FASTMCP_TRANSPORT=${MCP_TRANSPORT:-stdio}
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=${MCP_PORT:-8647}
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec python -c "from imf_data_mcp import mcp; mcp.run()"
else
  export FASTMCP_TRANSPORT=stdio
  exec python /mcp_http_proxy.py --port ${MCP_PORT:-8647} -- python -c "from imf_data_mcp import mcp; mcp.run()"
fi
