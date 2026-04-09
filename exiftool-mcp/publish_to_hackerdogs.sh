#!/usr/bin/env bash
set -euo pipefail
echo "Publishing exiftool-mcp..."
docker tag exiftool-mcp registry.hackerdogs.ai/exiftool-mcp:latest
docker push registry.hackerdogs.ai/exiftool-mcp:latest
echo "Done."
