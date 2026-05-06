#!/usr/bin/env bash
# Resume idx 175–180 only (ghunt, gitlab, gitleaks, globalping, gobuster, google-threat-intelligence).
# Appends to agent-index-171-180-test.log (does not truncate).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCKDIR="${ROOT}/.run_index_171_180_work.lockdir"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another 171-180 job is running (lock: $LOCKDIR). Wait or remove the directory." >&2
  exit 1
fi
_unlock() { rmdir "$LOCKDIR" 2>/dev/null || true; }
trap _unlock EXIT INT TERM

LOG="${ROOT}/agent-index-171-180-test.log"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-240}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"

_log() { printf '%s\n' "$1" >>"$LOG"; sync 2>/dev/null || true; }

_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp171python"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export PATH="${_SHIM}:$PATH"
fi

_log ""
_log "# --- partial 171-180 resume $(date -u +%Y-%m-%dT%H:%M:%SZ) dirs=ghunt..google-threat-intelligence ---"

dirs=(ghunt-mcp gitlab-mcp gitleaks-mcp globalping-mcp gobuster-mcp google-threat-intelligence-mcp)

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
tail -n 50 "$LOG"
