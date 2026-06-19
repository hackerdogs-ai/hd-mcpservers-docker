#!/usr/bin/env bash
# Batch 6: subjack-mcp, vulnerability-scanner-mcp, x8-mcp (5-step compliance each).
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/prep_mcp_python_path.sh"
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
cd "$ROOT"

servers=(
  subjack-mcp
  vulnerability-scanner-mcp
  x8-mcp
)

for s in "${servers[@]}"; do
  echo ""
  echo "######################################################################"
  echo "# BATCH6: $s"
  echo "######################################################################"
  set +e
  (cd "$s" && bash test.sh)
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then echo "### RESULT: $s PASS ###"
  else echo "### RESULT: $s FAIL (exit $ec) ###"
  fi
done
