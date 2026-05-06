#!/usr/bin/env bash
# Build Docker image if missing, then ./test.sh for simple-index lines 76-90.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=/dev/null
[[ -f "${ROOT}/scripts/mcp_test_bootstrap.sh" ]] && . "${ROOT}/scripts/mcp_test_bootstrap.sh"
export MCP_HTTP_STARTUP_SLEEP="${MCP_HTTP_STARTUP_SLEEP:-12}"
export MCP_HTTP_LIST_MAX_WAIT="${MCP_HTTP_LIST_MAX_WAIT:-90}"
export MCP_STDIO_DOCKER_TIMEOUT="${MCP_STDIO_DOCKER_TIMEOUT:-180}"

if ! docker info >/dev/null 2>&1; then echo "Docker not running" >&2; exit 1; fi

dirs=(
  aws-serverless-mcp
  aws-sns-sqs-mcp
  aws-stepfunctions-mcp
  aws-well-architected-security-mcp
  azure-mcp
  baidu-search-mcp-server-mcp
  baidusearch-mcp
  bearer-mcp
  bettercap-mcp
  bevigil-mcp
  binwalk-mcp
  bitbucket-mcp
  blackbird-mcp
  bloodhound-mcp-ai-mcp
  bloodhound-mcp
)

image_from_test() {
  local td="$1"
  local f="${td}/test.sh"
  [[ -f "$f" ]] || { echo ""; return; }
  sed -n 's/^IMAGE=["'\'']*\([^"'\'']*\)["'\'']*$/\1/p' "$f" | head -1
}

failed=()
for d in "${dirs[@]}"; do
  td="${ROOT}/${d}"
  echo "========== ${d} =========="
  if [[ ! -f "${td}/test.sh" ]]; then echo "SKIP (no test.sh)"; continue; fi
  IMG="$(image_from_test "$td")"
  if [[ -z "$IMG" ]]; then echo "SKIP (no IMAGE in test.sh)"; continue; fi
  if ! docker image inspect "$IMG" >/dev/null 2>&1; then
    echo "Building $IMG ..."
    docker build -t "$IMG" "$td" || true
    if ! docker image inspect "$IMG" >/dev/null 2>&1; then
      echo "RESULT ${d} FAIL (docker build)"
      failed+=("$d")
      continue
    fi
  fi
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
