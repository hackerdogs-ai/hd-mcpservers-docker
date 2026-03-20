#!/bin/sh

# This server proxies a remote Composio-hosted MCP endpoint.
# When placeholder keys are used, fall back to a mock server.
is_placeholder() {
  case "$RAPIDAPI_KEY" in
    *PLACEHOLDER*|"") return 0 ;;
    *) return 1 ;;
  esac
}

if is_placeholder; then
  MOCK_CMD="python3 /mock_mcp.py rapidapi-reverse-image-search-mcp 'RapidAPI reverse image search by CopySeeker' 8660"
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec $MOCK_CMD
  else
    exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8660} -- $MOCK_CMD
  fi
else
  if [ "$MCP_TRANSPORT" = "stdio" ]; then
    exec npx -y mcp-remote https://mcp.composio.dev/rapidapi/reverse-image-search-by-copyseeker
  else
    exec python3 /mcp_http_proxy.py --port ${MCP_PORT:-8660} -- npx -y mcp-remote https://mcp.composio.dev/rapidapi/reverse-image-search-by-copyseeker
  fi
fi
