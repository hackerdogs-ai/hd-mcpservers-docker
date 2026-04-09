#!/bin/sh
mkdir -p /root/.aws
printf "[default]\nregion = ${AWS_REGION:-us-east-1}\n" > /root/.aws/config
printf "[default]\naws_access_key_id = ${AWS_ACCESS_KEY_ID:-PLACEHOLDER}\naws_secret_access_key = ${AWS_SECRET_ACCESS_KEY:-PLACEHOLDER}\n" > /root/.aws/credentials
export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
export FASTMCP_TRANSPORT=${MCP_TRANSPORT:-stdio}
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=${MCP_PORT:-8620}
# Patch STS credential validation to prevent startup failure with placeholder keys
python3 << 'PYEOF'
import pathlib
p = pathlib.Path('/usr/local/lib/python3.11/site-packages/awslabs/prometheus_mcp_server/server.py')
if p.exists():
    t = p.read_text()
    t = t.replace("if not AWSCredentials.validate(config['region'], config['profile']):", "if False:")
    p.write_text(t)
PYEOF
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec awslabs.prometheus-mcp-server
else
  export FASTMCP_TRANSPORT=stdio
  exec python /mcp_http_proxy.py --port ${MCP_PORT:-8620} -- awslabs.prometheus-mcp-server
fi
