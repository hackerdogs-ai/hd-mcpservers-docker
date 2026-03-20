#!/bin/sh
export AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
export AWS_DEFAULT_PROFILE=
export FASTMCP_TRANSPORT=${MCP_TRANSPORT:-stdio}
export FASTMCP_HOST=0.0.0.0
export FASTMCP_PORT=${MCP_PORT:-8649}
if [ "$MCP_TRANSPORT" = "stdio" ]; then
  exec mcp-server-jira --jira-base-url "${JIRA_URL:-https://placeholder.atlassian.net}" --jira-token "${JIRA_API_TOKEN:-}"
else
  export FASTMCP_TRANSPORT=stdio
  exec python /mcp_http_proxy.py --port ${MCP_PORT:-8649} -- mcp-server-jira --jira-base-url "${JIRA_URL:-https://placeholder.atlassian.net}" --jira-token "${JIRA_API_TOKEN:-}"
fi
