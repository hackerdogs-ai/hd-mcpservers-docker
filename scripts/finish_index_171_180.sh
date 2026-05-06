#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
rmdir "${ROOT}/.run_index_171_180_work.lockdir" 2>/dev/null || true
cd "${ROOT}/scripts"
chmod +x run_index_171_180_tail5.sh
export MCP_STDIO_DOCKER_TIMEOUT=180 MCP_HTTP_STARTUP_SLEEP=12
./run_index_171_180_tail5.sh
cd "${ROOT}/ghunt-mcp"
export MCP_STDIO_DOCKER_TIMEOUT=360 MCP_HTTP_STARTUP_SLEEP=15
./test.sh
echo "finish_index_171_180: all steps OK"
