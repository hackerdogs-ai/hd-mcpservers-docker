#!/bin/bash
# Start the Tools Web Service API locally (no Docker) for testing.
# Run from the webservice directory. Uses .venv if present.

set -e
cd "$(dirname "$0")"

if [ -d ".venv" ]; then
    echo "Using virtualenv .venv"
    source .venv/bin/activate
else
    echo "No .venv found. Using system Python. Create one with: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

if [ -z "$TOOLS_CATALOG_URL" ] && [ -z "$TOOLS_CATALOG_S3_URI" ]; then
    if [ -f "catalog.json" ]; then
        export TOOLS_CATALOG_URL="file://$(pwd)/catalog.json"
        echo "Using catalog: file://$(pwd)/catalog.json"
    else
        echo "Warning: No catalog source set and no catalog.json found."
        echo "  Create catalog: python scripts/csv_to_catalog.py"
        echo "  Or set: export TOOLS_CATALOG_URL=file://$(pwd)/catalog.json"
    fi
fi

PORT="${PORT:-8000}"
echo "Starting API on http://0.0.0.0:${PORT}"
echo "  Health: http://localhost:${PORT}/health"
echo "  Docs:   http://localhost:${PORT}/docs"
exec python run.py

