#!/usr/bin/env bash
# Batch 9: censys-platform-mcp, github-mcp - 5-step compliance each (Batch 7/8 pattern).
#
# Steps (each test.sh -> scripts/mcp-five-step-compliance.sh):
#  [1] Docker image - hackerdogs/<dir>:latest exists (pull or build).
#  [2] Stdio - tools/list returns tools.
#  [3] Stdio - tools/call for one tool (remote_endpoint_info).
#  [4] HTTP streamable - tools/list after initialize + session.
#  [5] HTTP streamable - tools/call for the same tool.
#
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/prep_mcp_python_path.sh"
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
cd "$ROOT"

servers=(
  censys-platform-mcp
  github-mcp
)

for s in "${servers[@]}"; do
  echo ""
  echo "######################################################################"
  echo "# BATCH9: $s  (5-step compliance)"
  echo "######################################################################"
  set +e
  (cd "$s" && bash test.sh)
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then
    echo "### RESULT: $s PASS (all 5 compliance steps) ###"
  else
    echo "### RESULT: $s FAIL (exit $ec) ###"
  fi
done
