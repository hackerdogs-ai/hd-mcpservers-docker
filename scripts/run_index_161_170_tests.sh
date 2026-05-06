#!/usr/bin/env bash
# Compliance sweep for mcp-servers-simple-index.txt lines 161–170.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCKDIR="${ROOT}/.run_index_161_170_work.lockdir"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "run_index_161_170_tests.sh: another sweep is running (lock: ${LOCKDIR}). If none, remove that directory." >&2
  exit 1
fi
cleanup_lock() { rmdir "$LOCKDIR" 2>/dev/null || true; }
trap cleanup_lock EXIT INT TERM

LOG="${ROOT}/agent-index-161-170-test.log"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-240}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"
: >"$LOG"
_log_line() { printf '%s\n' "$1" >>"$LOG"; sync 2>/dev/null || true; }
_log_line "# sweep $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ MCP_STDIO_DOCKER_TIMEOUT=${MCP_STDIO_DOCKER_TIMEOUT}"

_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp161python"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export MCP_PYTHON="$_PY"
  export PATH="${_SHIM}:$PATH"
fi

dirs=(
  fierce-mcp file-operations-mcp financial-datasets-mcp firecrawl-mcp flights-mcp
  foremost-mcp fping-mcp fred-mcp garak-mcp gau-mcp
)

image_from_test_sh() {
  grep -m1 '^IMAGE=' "$1/test.sh" 2>/dev/null | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//" || true
}

for d in "${dirs[@]}"; do
  td="${ROOT}/${d}"
  _log_line "${d} START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ ! -f "${td}/test.sh" ]]; then _log_line "${d} SKIP no test.sh"; continue; fi
  img="$(image_from_test_sh "$td")"
  if [[ -z "$img" ]]; then _log_line "${d} SKIP no IMAGE"; continue; fi

  if ! docker image inspect "$img" >/dev/null 2>&1; then
    hd="hackerdogs/${d}:latest"
    if docker image inspect "$hd" >/dev/null 2>&1; then
      docker tag "$hd" "$img" && _log_line "${d} TAG ${hd} -> ${img}"
    else
      _log_line "${d} BUILD ${img} ..."
      if ! docker build -t "$img" "$td" >>"${TMPDIR:-/tmp}/build-${d}.log" 2>&1; then
        _log_line "${d} SKIP build failed"
        continue
      fi
      _log_line "${d} BUILD_OK"
    fi
  fi

  ec=0
  _log_line "${d} TEST_SH ..."
  ( cd "$td" && ./test.sh >>"${TMPDIR:-/tmp}/test-${d}.log" 2>&1 ) || ec=$?
  if [[ "$ec" -eq 0 ]]; then
    _log_line "${d} OK exit=0"
  else
    _log_line "${d} FAIL exit=${ec}"
  fi
done

echo "--- last 40 lines of ${LOG} ---"
tail -n 40 "$LOG"
