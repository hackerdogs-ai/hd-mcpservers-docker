#!/usr/bin/env bash
# Batch 5: image-tag verification batch (hackerdogs/*:latest) — mermaid, rapidapi copyseeker, reddit.
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/prep_mcp_python_path.sh"
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
cd "$ROOT"

servers=(
  mermaid-mcp
  rapidapi-hub-reverse-image-search-by-copyseeker-mcp
  reddit-mcp
)

for s in "${servers[@]}"; do
  echo ""
  echo "######################################################################"
  echo "# BATCH5: $s"
  echo "######################################################################"
  set +e
  (cd "$s" && bash test.sh)
  ec=$?
  set -e
  if [ "$ec" -eq 0 ]; then echo "### RESULT: $s PASS ###"
  else echo "### RESULT: $s FAIL (exit $ec) ###"
  fi
done
