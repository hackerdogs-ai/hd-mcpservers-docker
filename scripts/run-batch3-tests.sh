#!/usr/bin/env bash
# Use plain "set -eu" so this runs under older/bash-like shells that lack pipefail.
# Child test.sh scripts still use bash features.
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/prep_mcp_python_path.sh"
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
cd "$ROOT"

servers=(
  misp-mcp
  mobsf-mcp
  ms-fabric-rti-mcp
  n2yo-mcp
  naabu-mcp
  name-server-mcp
  nasa-mcp
  nbtscan-mcp
  ncrack-mcp
  nerva-mcp
)

for s in "${servers[@]}"; do
  echo ""
  echo "######################################################################"
  echo "# BATCH3: $s"
  echo "######################################################################"
  set +e
  (cd "$s" && bash test.sh)
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then echo "### RESULT: $s PASS ###"
  else echo "### RESULT: $s FAIL (exit $ec) ###"
  fi
done
