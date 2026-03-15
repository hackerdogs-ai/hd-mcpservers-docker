#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../" && pwd)"

ENV_FILE="${REPO_ROOT}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: .env not found at ${ENV_FILE}" >&2
  echo "Create it and set MASTER_KEY=... (and optionally GLRAI_CONTEXT=...)." >&2
  exit 1
fi

# Load env vars (including MASTER_KEY) from repo root .env
set -a
# shellcheck disable=SC1090
. "${ENV_FILE}"
set +a

if [[ -z "${MASTER_KEY:-}" ]]; then
  echo "ERROR: MASTER_KEY is not set in ${ENV_FILE}" >&2
  exit 1
fi

echo "Starting Google Local Results AI Server via Docker Compose..."
echo "- compose: ${SCRIPT_DIR}/docker-compose-serpapi-good-local-results-ai.yml"
echo "- MASTER_KEY: [loaded]"
echo "- GLRAI_CONTEXT: ${GLRAI_CONTEXT:-"(default ../../../../google-local-results-ai-server)"}"

if docker compose version >/dev/null 2>&1; then
  DC=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  DC=(docker-compose)
else
  echo "ERROR: Neither 'docker compose' nor 'docker-compose' is available in PATH." >&2
  exit 1
fi

"${DC[@]}" \
  --project-name hd-serpapi-good-local-results-ai \
  -f "${SCRIPT_DIR}/docker-compose-serpapi-good-local-results-ai.yml" \
  up -d --build

echo "Up. Server should be available at http://localhost:8000"


