#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/prep_mcp_python_path.sh"
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
cd "$ROOT"

servers=(
  netcat-mcp
  netdiscover-mcp
  netexec-mcp
  netutils-mcp
  ngrep-mcp
  nikto-mcp
  nmap-mcp
  nosqlmap-mcp
  notion-mcp
  nova-framework-mcp
)

for s in "${servers[@]}"; do
  echo ""
  echo "######################################################################"
  echo "# BATCH4: $s"
  echo "######################################################################"
  set +e
  (cd "$s" && bash test.sh)
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then echo "### RESULT: $s PASS ###"
  else echo "### RESULT: $s FAIL (exit $ec) ###"
  fi
done
