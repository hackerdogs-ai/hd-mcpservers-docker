#!/bin/sh
mkdir -p /root/.aws
printf "[default]\nregion = ${AWS_REGION:-us-east-1}\n" > /root/.aws/config
printf "[default]\naws_access_key_id = ${AWS_ACCESS_KEY_ID:-PLACEHOLDER}\naws_secret_access_key = ${AWS_SECRET_ACCESS_KEY:-PLACEHOLDER}\n" > /root/.aws/credentials
export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
export AWS_PROFILE=default
export AWS_CONFIG_FILE=/root/.aws/config
export AWS_SHARED_CREDENTIALS_FILE=/root/.aws/credentials

# Fallback chain for the port: test runner's PORT -> MCP_PORT -> 8080
TARGET_PORT=${PORT:-${MCP_PORT:-8080}}

export FASTMCP_HOST=0.0.0.0

# If the runner explicitly asks for stdio, OR if it doesn't specify any HTTP transport flags
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  export FASTMCP_TRANSPORT=stdio
  exec awslabs.aws-bedrock-custom-model-import-mcp-server
else
  # HTTP / Proxy mode
  echo "[entrypoint] Starting HTTP proxy on port $TARGET_PORT..."
  export FASTMCP_TRANSPORT=stdio
  exec python /mcp_http_proxy.py --port $TARGET_PORT -- awslabs.aws-bedrock-custom-model-import-mcp-server
fi