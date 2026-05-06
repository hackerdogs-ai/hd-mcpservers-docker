#!/usr/bin/env bash
# Stdio + HTTP streamable compliance for simple-index lines 130-139 (images must exist; no docker build).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-180}"
export MCP_STDIO_STDIN_EOF_DELAY_MS="${MCP_STDIO_STDIN_EOF_DELAY_MS:-400}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"
export MCP_HTTP_LIST_MAX_WAIT="${MCP_HTTP_LIST_MAX_WAIT:-90}"

_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp130139python"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export PATH="${_SHIM}:$PATH"
fi

if ! docker info >/dev/null 2>&1; then echo "Docker not running" >&2; exit 1; fi

dirs=(
  deepwebresearch-mcp
  dependency-check-mcp
  dharma-mcp
  dirb-mcp
  dirsearch-mcp
  dns-mcp-server-mcp
  dnsdumpster-mcp
  dnsenum-mcp
  dnsreaper-mcp
  dnsrecon-mcp
)

failed=()
for d in "${dirs[@]}"; do
  td="${ROOT}/${d}"
  echo "========== ${d} =========="
  if [[ ! -f "${td}/test.sh" ]]; then echo "SKIP ${d} (no test.sh)"; continue; fi
  if ( cd "$td" && ./test.sh ); then
    echo "RESULT ${d} OK"
  else
    echo "RESULT ${d} FAIL"
    failed+=("$d")
  fi
done

if ((${#failed[@]})); then
  echo "--- Failed: ${failed[*]} ---"
  exit 1
fi
echo "--- All OK ---"
exit 0
