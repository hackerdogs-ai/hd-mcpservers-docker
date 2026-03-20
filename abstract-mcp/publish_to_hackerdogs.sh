#!/usr/bin/env bash
set -euo pipefail
echo "Publishing abstract-mcp to HackerDogs registry..."
docker tag abstract-mcp registry.hackerdogs.ai/abstract-mcp:latest
docker push registry.hackerdogs.ai/abstract-mcp:latest
echo "Done."
