#!/usr/bin/env bash
# Batch 8: remote-reference stub set (8 servers) — same layout as xpoz-mcp-server-mcp
# (FastMCP stub Dockerfile + test.sh → scripts/mcp-five-step-compliance.sh).
#
# ── Five compliance criteria (must all pass) ─────────────────────────────────
#  [1] Docker image — image hackerdogs/<dir>:latest exists (pull or build from Dockerfile).
#  [2] Stdio — JSON-RPC tools/list returns a non-empty tools array.
#  [3] Stdio — JSON-RPC tools/call succeeds for the batch-declared tool (result | content | error).
#  [4] HTTP (streamable) — POST /mcp tools/list returns tools after initialize + session.
#  [5] HTTP (streamable) — POST /mcp tools/call succeeds for the same tool as [3].
#
# Implementation: scripts/mcp-five-step-compliance.sh
# Reference server: xpoz-mcp-server-mcp (listed first below).
# ─────────────────────────────────────────────────────────────────────────────
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/prep_mcp_python_path.sh"
export PATH="/c/Program Files/Docker/Docker/resources/bin:$PATH"
cd "$ROOT"

servers=(
  xpoz-mcp-server-mcp
  whoisxmlapi-mcp
  tools-to-migrate-to-mcp
  tavily-remote-mcp
  serpapi-mcp
  prowler-mcp
  mitre-attack-remote-mcp
  mcp-docker-mcp
)

for s in "${servers[@]}"; do
  echo ""
  echo "######################################################################"
  echo "# BATCH8: $s  (criteria 1–5 via test.sh)"
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
