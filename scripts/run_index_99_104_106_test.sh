#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "${ROOT}/scripts/mcp_test_bootstrap.sh" ]] && . "${ROOT}/scripts/mcp_test_bootstrap.sh"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"
export MCP_HTTP_LIST_MAX_WAIT="${MCP_HTTP_LIST_MAX_WAIT:-120}"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-180}"
if ! docker info >/dev/null 2>&1; then echo "Docker not running" >&2; exit 1; fi
dirs=( bully-mcp capa-mcp cero-mcp certgraph-mcp certipy-mcp checkov-mcp chrome-devtools-mcp )
failed=()
for d in "${dirs[@]}"; do
  echo "========== ${d} =========="
  [[ ! -f "${ROOT}/${d}/test.sh" ]] && { echo "SKIP"; continue; }
  if ( cd "${ROOT}/${d}" && ./test.sh ); then echo "RESULT ${d} OK"; else echo "RESULT ${d} FAIL"; failed+=("$d"); fi
done
if ((${#failed[@]})); then echo "--- Failed: ${failed[*]} ---"; exit 1; fi
echo "--- All OK ---"
exit 0