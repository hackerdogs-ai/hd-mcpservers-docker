#!/usr/bin/env bash
# Fast path: idx 176–180 only (skip ghunt). Appends to agent-index-171-180-test.log.
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
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-120}"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-10}"
_log() { printf '%s\n' "$1" >>"$LOG"; sync 2>/dev/null || true; }
_log ""
_log "# --- tail5 $(date -u +%Y-%m-%dT%H:%M:%SZ) MCP_STDIO_DOCKER_TIMEOUT=${MCP_STDIO_DOCKER_TIMEOUT} ---"
_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
[[ -x "$_PY" ]] && { _SH="${TMPDIR:-/tmp}/mcp171t5"; mkdir -p "$_SH"; printf '%s\n' "#!/bin/sh" "exec '$_PY' \"\$@\"" >"${_SH}/python"; chmod +x "${_SH}/python"; export PATH="${_SH}:$PATH"; }
image_from_test_sh() { grep -m1 '^IMAGE=' "$1/test.sh" 2>/dev/null | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//" || true; }
for d in gitlab-mcp gitleaks-mcp globalping-mcp gobuster-mcp google-threat-intelligence-mcp; do
  td="${ROOT}/${d}"
  _log "${d} START $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  img="$(image_from_test_sh "$td")"
  if ! docker image inspect "$img" >/dev/null 2>&1; then
    hd="hackerdogs/${d}:latest"
    if docker image inspect "$hd" >/dev/null 2>&1; then docker tag "$hd" "$img" && _log "${d} TAG"; else
      _log "${d} BUILD ${img} ..."
      if ! docker build -t "$img" "$td" >>"${TMPDIR:-/tmp}/b-${d}.log" 2>&1; then
        if docker image inspect "$img" >/dev/null 2>&1; then _log "${d} BUILD_OK (image present after race)"
        else _log "${d} SKIP build failed"; continue
        fi
      else _log "${d} BUILD_OK"
      fi
    fi
  fi
  ec=0; _log "${d} TEST_SH"; ( cd "$td" && ./test.sh >>"${TMPDIR:-/tmp}/t-${d}.log" 2>&1 ) || ec=$?
  [[ "$ec" -eq 0 ]] && _log "${d} OK exit=0" || _log "${d} FAIL exit=${ec}"
done
tail -n 25 "$LOG"
