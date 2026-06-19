#!/usr/bin/env bash
# Batch 7: runtime/protocol recovery set (8 servers)
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/prep_mcp_python_path.sh"
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
cd "$ROOT"

servers=(
  nasa-mcp
  octagon-mcp-server-mcp
  postman-mcp
  s3-mcp-server-mcp
  search1api-mcp
  serper-search-mcp
  steampipe-mcp
  winston-ai-mcp
)

for s in "${servers[@]}"; do
  echo ""
  echo "######################################################################"
  echo "# BATCH7: $s"
  echo "######################################################################"
  set +e
  (cd "$s" && bash test.sh)
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then
    echo "### RESULT: $s PASS ###"
  else
    echo "### RESULT: $s FAIL (exit $ec) ###"
  fi
done

