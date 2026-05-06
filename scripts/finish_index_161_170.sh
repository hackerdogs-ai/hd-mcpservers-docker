#!/usr/bin/env bash
# One-shot: rebuild flights+fred images, run resume tests (flights..gau), clear EXCEPTIONS + note O, rebuild status table.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if ! docker info >/dev/null 2>&1; then
  echo "finish_index_161_170.sh: Docker is not reachable (start Docker Desktop and wait until it is ready)." >&2
  exit 1
fi

echo "==> docker build flights-mcp"
docker build -t hackerdogs/flights-mcp:latest "$ROOT/flights-mcp"
echo "==> docker build fred-mcp"
docker build -t hackerdogs/fred-mcp:latest "$ROOT/fred-mcp"

# Stale lockdir from a killed sweep blocks resume; remove only if empty.
rmdir "$ROOT/.run_index_161_170_work.lockdir" 2>/dev/null || true

echo "==> run_index_161_170_resume.sh (flights, fping, fred, garak, gau)"
if ! "$ROOT/scripts/run_index_161_170_resume.sh"; then
  echo "finish_index_161_170.sh: tests failed — see $ROOT/agent-index-161-170-test.log" >&2
  exit 1
fi

py -3 "$ROOT/scripts/_finalize_161_170_exceptions.py"
py -3 "$ROOT/scripts/_rebuild_stdio_http_status.py"
echo "==> Idx 161–170 exceptions cleared and mcp-servers-stdio-http-streamable-status.txt regenerated."
