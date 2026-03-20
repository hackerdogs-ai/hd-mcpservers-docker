#!/usr/bin/env bash
set -euo pipefail
echo "Publishing webc-mcp..."
docker tag webc-mcp registry.hackerdogs.ai/webc-mcp:latest
docker push registry.hackerdogs.ai/webc-mcp:latest
echo "Done."
