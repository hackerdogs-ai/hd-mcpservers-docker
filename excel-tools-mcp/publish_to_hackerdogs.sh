#!/usr/bin/env bash
set -euo pipefail
echo "Publishing excel-tools-mcp..."
docker tag excel-tools-mcp registry.hackerdogs.ai/excel-tools-mcp:latest
docker push registry.hackerdogs.ai/excel-tools-mcp:latest
echo "Done."
