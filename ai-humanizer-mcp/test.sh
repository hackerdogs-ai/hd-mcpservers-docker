#!/usr/bin/env bash
# Six-step MCP test: build → stdio list/call → HTTP list/call → teardown.
# Shared logic: ../scripts/mcp-standard-six-test.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_SCRIPTS="$(cd "$SCRIPT_DIR/../scripts" && pwd)"

export MCP_PROJECT_DIR="$SCRIPT_DIR"
export MCP_IMAGE="ai-humanizer-mcp"
export MCP_PORT=8601
export MCP_CONTAINER="ai-humanizer-mcp-test"
export MCP_TOOL_NAME="detect"
export MCP_TOOL_ARGUMENTS='{"type":"original_text","text":"Hello world","detectionTypeList":["HEMINGWAY"]}'
export MCP_EXTRA_DOCKER_ARGS=""

exec bash "$REPO_SCRIPTS/mcp-standard-six-test.sh"
