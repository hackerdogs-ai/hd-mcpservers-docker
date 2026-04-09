#!/bin/bash
set -e
IMAGE_NAME="opencv-mcp-server-mcp"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DO_BUILD=false; DO_PUBLISH=false
while [[ $# -gt 0 ]]; do case $1 in --build) DO_BUILD=true; shift;; --publish) DO_PUBLISH=true; shift;; --help|-h) echo "Usage: $0 [--build] [--publish] [dockerhub_user] [tag]"; exit 0;; *) ARGS+=("$1"); shift;; esac; done
[ "$DO_BUILD" = false ] && [ "$DO_PUBLISH" = false ] && DO_BUILD=true
cd "$PROJECT_ROOT"
TAG="${ARGS[1]:-latest}"
if [ "$DO_BUILD" = true ]; then docker build -t "hackerdogs/${IMAGE_NAME}:${TAG}" .; echo "Built hackerdogs/${IMAGE_NAME}:${TAG}"; fi
if [ "$DO_PUBLISH" = true ]; then USER="${ARGS[0]:-hackerdogs}"; docker push "${USER}/${IMAGE_NAME}:${TAG}"; echo "Pushed ${USER}/${IMAGE_NAME}:${TAG}"; fi
