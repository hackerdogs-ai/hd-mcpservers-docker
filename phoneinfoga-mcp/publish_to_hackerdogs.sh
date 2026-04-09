#!/usr/bin/env bash
set -euo pipefail
echo "Publishing phoneinfoga-mcp..."
docker tag phoneinfoga-mcp registry.hackerdogs.ai/phoneinfoga-mcp:latest
docker push registry.hackerdogs.ai/phoneinfoga-mcp:latest
echo "Done."
