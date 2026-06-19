#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MCP_FIVE_PROJECT_DIR="$PROJECT_DIR"
export MCP_FIVE_IMAGE="hackerdogs/github-mcp:latest"
export MCP_FIVE_PORT=8521
export MCP_FIVE_CONTAINER="github-mcp-test"
export MCP_FIVE_TITLE="GitHub MCP - remote reference stub - 5-step compliance"
export MCP_FIVE_TOOL_NAME="remote_endpoint_info"
export MCP_FIVE_TOOL_ARGS_JSON='{}'
export MCP_FIVE_STDIO_SLEEP="${MCP_FIVE_STDIO_SLEEP:-6}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-12}"
exec bash "$PROJECT_DIR/../scripts/mcp-five-step-compliance.sh"
