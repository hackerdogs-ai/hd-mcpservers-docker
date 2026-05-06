#!/usr/bin/env bash
# Quick stdio + HTTP streamable check for idx 169–170 (garak-mcp, gau-mcp).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp169py"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export MCP_PYTHON="$_PY" PATH="${_SHIM}:$PATH"
fi
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-180}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-12}"

docker stop garak-mcp-test gau-mcp-test 2>/dev/null || true
docker rm -f garak-mcp-test gau-mcp-test 2>/dev/null || true

for d in garak-mcp gau-mcp; do
  echo "======== ${d} ========"
  td="${ROOT}/${d}"
  img="$(grep -m1 '^IMAGE=' "${td}/test.sh" | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//")"
  if ! docker image inspect "$img" >/dev/null 2>&1; then
    echo "BUILD ${img}"
    docker build -t "$img" "$td"
  fi
  ( cd "$td" && ./test.sh )
  echo "${d} DONE exit=$?"
done
