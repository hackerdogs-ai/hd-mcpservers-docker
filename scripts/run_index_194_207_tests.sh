#!/usr/bin/env bash
# Compliance sweep for mcp-servers-simple-index.txt lines 194–207.
# Builds missing image when possible; tags hackerdogs/<dir>:latest -> IMAGE when test uses short name.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOCKDIR="${ROOT}/.run_index_194_207_tests.lockdir"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "run_index_194_207_tests.sh: another sweep is running (lock: ${LOCKDIR}). If none, remove that directory." >&2
  exit 1
fi
cleanup_lock() { rmdir "$LOCKDIR" 2>/dev/null || true; }
trap cleanup_lock EXIT INT TERM

LOG="${ROOT}/agent-index-194-207-test.log"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-120}"
: >"$LOG"
echo "# sweep $(date -u +%Y-%m-%dT%H:%M:%SZ) pid=$$ MCP_STDIO_DOCKER_TIMEOUT=${MCP_STDIO_DOCKER_TIMEOUT}" >>"$LOG"

# Many test.sh scripts invoke `python`; Git Bash often only has Windows Python on disk.
_PY="/c/Users/${USERNAME:-$USER}/AppData/Local/Python/pythoncore-3.14-64/python.exe"
if [[ -x "$_PY" ]]; then
  _SHIM="${TMPDIR:-/tmp}/mcp194python"
  mkdir -p "$_SHIM"
  cat >"${_SHIM}/python" <<EOF
#!/bin/sh
exec '$_PY' "\$@"
EOF
  chmod +x "${_SHIM}/python" 2>/dev/null || true
  export PATH="${_SHIM}:$PATH"
fi

dirs=(
  http-headers-security-mcp httpx-mcp hydra-mcp imf-data-mcp ipinfo-mcp iplocate-mcp ivre-mcp
  jaeles-mcp jira-mcp john-mcp joomscan-mcp julius-mcp jwt-tool-mcp katana-mcp
)

image_from_test_sh() {
  grep -m1 '^IMAGE=' "$1/test.sh" 2>/dev/null | sed -E "s/^IMAGE=[\"']?//;s/[\"']?\$//" || true
}

for d in "${dirs[@]}"; do
  td="${ROOT}/${d}"
  if [[ ! -f "${td}/test.sh" ]]; then echo "${d} SKIP no test.sh" >>"$LOG"; continue; fi
  img="$(image_from_test_sh "$td")"
  if [[ -z "$img" ]]; then echo "${d} SKIP no IMAGE" >>"$LOG"; continue; fi

  if ! docker image inspect "$img" >/dev/null 2>&1; then
    hd="hackerdogs/${d}:latest"
    if docker image inspect "$hd" >/dev/null 2>&1; then
      docker tag "$hd" "$img" && echo "${d} TAG ${hd} -> ${img}" >>"$LOG"
    else
      echo "${d} BUILD ${img} ..." >>"$LOG"
      if ! docker build -t "$img" "$td" >>"${TMPDIR:-/tmp}/build-${d}.log" 2>&1; then
        echo "${d} SKIP build failed" >>"$LOG"
        continue
      fi
    fi
  fi

  ec=0
  ( cd "$td" && ./test.sh >>"${TMPDIR:-/tmp}/test-${d}.log" 2>&1 ) || ec=$?
  if [[ "$ec" -eq 0 ]]; then
    echo "${d} OK exit=0" >>"$LOG"
  else
    echo "${d} FAIL exit=${ec}" >>"$LOG"
  fi
done

cat "$LOG"
