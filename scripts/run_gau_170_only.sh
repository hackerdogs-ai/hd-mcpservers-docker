#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp170py"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export MCP_PYTHON="$_PY" PATH="${_SHIM}:$PATH"
fi
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-180}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"
docker rm -f gau-mcp-test 2>/dev/null || true
td="${ROOT}/gau-mcp"
img="$(grep -m1 '^IMAGE=' "${td}/test.sh" | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//")"
if ! docker image inspect "$img" >/dev/null 2>&1; then
  docker build -t "$img" "$td"
fi
( cd "$td" && ./test.sh )
