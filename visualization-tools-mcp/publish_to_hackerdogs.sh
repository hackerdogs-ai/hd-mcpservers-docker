#!/usr/bin/env bash
set -euo pipefail
echo "Publishing visualization-tools-mcp..."
docker tag visualization-tools-mcp registry.hackerdogs.ai/visualization-tools-mcp:latest
docker push registry.hackerdogs.ai/visualization-tools-mcp:latest
echo "Done."
