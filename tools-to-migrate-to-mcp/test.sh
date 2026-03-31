#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export MCP_FIVE_PROJECT_DIR="$PROJECT_DIR"
export MCP_FIVE_IMAGE="hackerdogs/tools-to-migrate-to-mcp:latest"
export MCP_FIVE_PORT=8512
export MCP_FIVE_CONTAINER="tools-to-migrate-to-mcp-test"
export MCP_FIVE_TITLE="tools-to-migrate workspace — placeholder MCP — 5-step compliance"
export MCP_FIVE_TOOL_NAME="workspace_status"
export MCP_FIVE_TOOL_ARGS_JSON='{}'
export MCP_FIVE_STDIO_SLEEP="${MCP_FIVE_STDIO_SLEEP:-6}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-12}"
exec bash "$PROJECT_DIR/../scripts/mcp-five-step-compliance.sh"
