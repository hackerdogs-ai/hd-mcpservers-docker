#!/usr/bin/env bash
# Resume 161–170: re-run flights (after timing fix), then fping → gau if sweep stopped mid-way.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCKDIR="${ROOT}/.run_index_161_170_work.lockdir"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "run_index_161_170_resume.sh: lock busy (${LOCKDIR})" >&2
  exit 1
fi
cleanup_lock() { rmdir "$LOCKDIR" 2>/dev/null || true; }
trap cleanup_lock EXIT INT TERM

LOG="${ROOT}/agent-index-161-170-test.log"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-240}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-15}"
_log_line() { printf '%s\n' "$1" >>"$LOG"; sync 2>/dev/null || true; }
_log_line "# resume $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$"

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

dirs=(flights-mcp fping-mcp fred-mcp garak-mcp gau-mcp)
any_fail=0
image_from_test_sh() {
  grep -m1 '^IMAGE=' "$1/test.sh" 2>/dev/null | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//" || true
}

for d in "${dirs[@]}"; do
  td="${ROOT}/${d}"
  _log_line "${d} RESUME_START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  [[ ! -f "${td}/test.sh" ]] && { _log_line "${d} SKIP no test.sh"; continue; }
  img="$(image_from_test_sh "$td")"
  [[ -z "$img" ]] && { _log_line "${d} SKIP no IMAGE"; continue; }
  if ! docker image inspect "$img" >/dev/null 2>&1; then
    hd="hackerdogs/${d}:latest"
    if docker image inspect "$hd" >/dev/null 2>&1; then
      docker tag "$hd" "$img" && _log_line "${d} TAG ${hd} -> ${img}"
    else
      _log_line "${d} BUILD ${img} ..."
      if ! docker build -t "$img" "$td" >>"${TMPDIR:-/tmp}/build-${d}.log" 2>&1; then
        _log_line "${d} SKIP build failed"
        any_fail=1
        continue
      fi
      _log_line "${d} BUILD_OK"
    fi
  fi
  ec=0
  _log_line "${d} TEST_SH ..."
  ( cd "$td" && ./test.sh >>"${TMPDIR:-/tmp}/test-${d}.log" 2>&1 ) || ec=$?
  if [[ "$ec" -eq 0 ]]; then _log_line "${d} OK exit=0"; else _log_line "${d} FAIL exit=${ec}"; any_fail=1; fi
done

tail -n 25 "$LOG"
exit "$any_fail"
