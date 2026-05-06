#!/usr/bin/env bash
# Quick sweep: idx 152–160 (exa-mcp … ffuf-mcp). Shorter MCP timeouts than run_index_152_160_tests.sh.
# Skips a server if: docker build exceeds MCP152160_BUILD_MAX_SEC, build fails, or Dockerfile/engine error.
# Does NOT raise the 480s stdio floor (unlike the full 152–160 sweep) — Node cold starts may FAIL under short waits.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCKDIR="${ROOT}/.run_index_152_160_quick.lockdir"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "run_index_152_160_tests_quick_skip.sh: lock busy (${LOCKDIR})" >&2
  exit 1
fi
cleanup_lock() { rmdir "$LOCKDIR" 2>/dev/null || true; }
trap cleanup_lock EXIT INT TERM

# Shorter compliance waits (override any inherited huge values)
export MCP_STDIO_DOCKER_TIMEOUT="${MCP152160_STDIO_TIMEOUT:-90}"
export MCP_STDIO_STDIN_EOF_DELAY_MS="${MCP152160_STDIN_EOF_MS:-350}"
export MCP_HTTP_STARTUP_SLEEP="${MCP152160_HTTP_SLEEP:-10}"
export MCP_HTTP_LIST_MAX_WAIT="${MCP152160_HTTP_LIST_WAIT:-45}"

BUILD_MAX_SEC="${MCP152160_BUILD_MAX_SEC:-300}"

LOG="${ROOT}/agent-index-152-160-quick-test.log"
: >"$LOG"
_log() { printf '%s\n' "$1" | tee -a "$LOG"; }

_log "# quick sweep $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ stdio=${MCP_STDIO_DOCKER_TIMEOUT}s http_sleep=${MCP_HTTP_STARTUP_SLEEP}s list_wait=${MCP_HTTP_LIST_MAX_WAIT}s build_max=${BUILD_MAX_SEC}s"

if ! docker info >/dev/null 2>&1; then
  _log "ERROR: Docker not reachable."
  exit 1
fi

_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp152qpython"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export PATH="${_SHIM}:$PATH"
fi

dirs=(
  exa-mcp excel-tools-mcp exiftool-agent-mcp exiftool-mcp exploitdb-mcp
  falco-mcp feroxbuster-mcp fetch-mcp ffuf-mcp
)

image_from_test_sh() {
  grep -m1 '^IMAGE=' "$1/test.sh" 2>/dev/null | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//" || true
}

run_with_build_timeout() {
  local logf="$1"
  shift
  if command -v timeout >/dev/null 2>&1; then
    timeout "${BUILD_MAX_SEC}" "$@" >>"$logf" 2>&1
    local ec=$?
    if [[ "$ec" -eq 124 ]]; then
      return 124
    fi
    return "$ec"
  fi
  "$@" >>"$logf" 2>&1
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
      btmp="${TMPDIR:-/tmp}/build-quick-${d}-$$.log"
      _log "${d} BUILD ${img} (max ${BUILD_MAX_SEC}s) ..."
      ec=0
      run_with_build_timeout "$btmp" docker build -t "$img" "$td" || ec=$?
      if [[ "$ec" -eq 124 ]]; then
        _log "${d} SKIP docker build exceeded ${BUILD_MAX_SEC}s"
        continue
      fi
      if ! docker image inspect "$img" >/dev/null 2>&1; then
        _log "${d} SKIP build failed (see ${btmp})"
        continue
      fi
      _log "${d} BUILD_OK"
    fi
  fi

  ttmp="${TMPDIR:-/tmp}/test-quick-${d}-$$.log"
  ec=0
  _log "${d} TEST_SH ..."
  ( cd "$td" && ./test.sh >"$ttmp" 2>&1 ) || ec=$?
  if [[ "$ec" -eq 0 ]]; then
    _log "${d} OK exit=0"
  else
    _log "${d} FAIL exit=${ec} (log ${ttmp})"
    tail -n 25 "$ttmp" >>"$LOG" || true
  fi
done

_log "--- done ---"
