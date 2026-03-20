#!/usr/bin/env bash
set -euo pipefail
echo "Publishing powerpoint-tools-mcp..."
docker tag powerpoint-tools-mcp registry.hackerdogs.ai/powerpoint-tools-mcp:latest
docker push registry.hackerdogs.ai/powerpoint-tools-mcp:latest
echo "Done."
