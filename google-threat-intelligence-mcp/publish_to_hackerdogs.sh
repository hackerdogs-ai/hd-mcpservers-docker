#!/bin/bash
set -euo pipefail
IMAGE="hackerdogs/google-threat-intelligence-mcp"
TAG="${1:-latest}"
echo "Building and pushing $IMAGE:$TAG ..."
docker buildx build --platform linux/amd64,linux/arm64 -t "$IMAGE:$TAG" --push .
echo "Done: $IMAGE:$TAG"
