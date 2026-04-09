#!/bin/sh
mkdir -p /root/.aws
printf "[default]\nregion = ${AWS_REGION:-us-east-1}\n" > /root/.aws/config
printf "[default]\naws_access_key_id = ${AWS_ACCESS_KEY_ID:-PLACEHOLDER}\naws_secret_access_key = ${AWS_SECRET_ACCESS_KEY:-PLACEHOLDER}\n" > /root/.aws/credentials
export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
export FASTMCP_TRANSPORT=${MCP_TRANSPORT:-stdio}
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=${MCP_PORT:-8624}
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec awslabs.amazon-sns-sqs-mcp-server
else
  export FASTMCP_TRANSPORT=stdio
  exec python /mcp_http_proxy.py --port ${MCP_PORT:-8624} -- awslabs.amazon-sns-sqs-mcp-server
fi
