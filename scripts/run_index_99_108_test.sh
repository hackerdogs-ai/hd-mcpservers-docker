#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "${ROOT}/scripts/mcp_test_bootstrap.sh" ]] && . "${ROOT}/scripts/mcp_test_bootstrap.sh"
if [[ "${MCP_QUICK:-0}" == "1" ]]; then
  export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-8}"
  export MCP_HTTP_LIST_MAX_WAIT="${MCP_HTTP_LIST_MAX_WAIT:-45}"
  export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-90}"
else
  export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"
  export MCP_HTTP_LIST_MAX_WAIT="${MCP_HTTP_LIST_MAX_WAIT:-120}"
  export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-240}"
fi
if ! docker info >/dev/null 2>&1; then echo "Docker not running" >&2; exit 1; fi
dirs=( bully-mcp capa-mcp cero-mcp certgraph-mcp certipy-mcp checkov-mcp checksec-mcp chrome-devtools-mcp cisco-mcp-scanner-mcp clair-mcp )
failed=()
for d in "${dirs[@]}"; do
  td="${ROOT}/${d}"
  echo "========== ${d} =========="
  [[ ! -f "${td}/test.sh" ]] && { echo "SKIP"; continue; }
  if ( cd "$td" && ./test.sh ); then echo "RESULT ${d} OK"; else echo "RESULT ${d} FAIL"; failed+=("$d"); fi
done
if ((${#failed[@]})); then echo "--- Failed: ${failed[*]} ---"; exit 1; fi
echo "--- All OK ---"
exit 0