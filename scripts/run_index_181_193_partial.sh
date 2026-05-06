#!/usr/bin/env bash
# Re-run compliance for idx 182 + 188–193 only (gowitness + hashcat … horusec).
# Appends to agent-index-181-193-test.log (does not truncate the full sweep file).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="${ROOT}/agent-index-181-193-test.log"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-240}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"

_log() { printf '%s\n' "$1" >>"$LOG"; sync 2>/dev/null || true; }

_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp181python"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export PATH="${_SHIM}:$PATH"
fi

_log ""
_log "# --- partial sweep $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ dirs=gowitness,hashcat,hashid,hashpump,hibp,holehe,horusec MCP_STDIO_DOCKER_TIMEOUT=${MCP_STDIO_DOCKER_TIMEOUT} ---"

dirs=(gowitness-mcp hashcat-mcp hashid-mcp hashpump-mcp hibp-mcp holehe-mcp horusec-mcp)

image_from_test_sh() {
  grep -m1 '^IMAGE=' "$1/test.sh" 2>/dev/null | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//" || true
}

for d in "${dirs[@]}"; do
  td="${ROOT}/${d}"
  _log "${d} START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ ! -f "${td}/test.sh" ]]; then _log "${d} SKIP no test.sh"; continue; fi
  img="$(image_from_test_sh "$td")"
  if [[ -z "$img" ]]; then _log "${d} SKIP no IMAGE"; continue; fi

  if ! docker image inspect "$img" >/dev/null 2>&1; then
    hd="hackerdogs/${d}:latest"
    if docker image inspect "$hd" >/dev/null 2>&1; then
      docker tag "$hd" "$img" && _log "${d} TAG ${hd} -> ${img}"
    else
      _log "${d} BUILD ${img} ..."
      if ! docker build -t "$img" "$td" >>"${TMPDIR:-/tmp}/build-${d}.log" 2>&1; then
        _log "${d} SKIP build failed"
        continue
      fi
      _log "${d} BUILD_OK"
    fi
  fi

  ec=0
  _log "${d} TEST_SH ..."
  ( cd "$td" && ./test.sh >>"${TMPDIR:-/tmp}/test-${d}.log" 2>&1 ) || ec=$?
  if [[ "$ec" -eq 0 ]]; then
    _log "${d} OK exit=0"
  else
    _log "${d} FAIL exit=${ec}"
  fi
done

echo "--- tail of ${LOG} ---"
tail -n 45 "$LOG"
