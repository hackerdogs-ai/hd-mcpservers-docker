#!/bin/bash
# Build and push osint-tools to Docker Hub: multi-arch (amd64 + arm64), tags <version> and latest.
# Usage: ./publish_osint_tools.sh <username> [version]
# Example: ./publish_osint_tools.sh hackerdogs v1.0.0
# Example: ./publish_osint_tools.sh hackerdogs   (uses version "latest")
# Run from anywhere; script cd's to its own dir for the build.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

if [ -z "$1" ]; then
    echo "Usage: $0 <dockerhub_username> [version]"
    echo "Example: $0 hackerdogs v1.0.0"
    exit 1
fi

DOCKERHUB_USERNAME="$1"
VERSION="${2:-latest}"
IMAGE_NAME="osint-tools"
FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}"

echo "Publishing ${FULL_IMAGE_NAME}:${VERSION} and :latest (linux/amd64 + linux/arm64)"
echo ""

command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker not found${NC}"; exit 1; }
docker buildx version >/dev/null 2>&1 || { echo -e "${RED}Docker Buildx required${NC}"; exit 1; }

BUILDER_NAME="osint-multiarch-builder"
docker buildx inspect "$BUILDER_NAME" >/dev/null 2>&1 || docker buildx create --name "$BUILDER_NAME" --use --bootstrap
docker buildx use "$BUILDER_NAME" >/dev/null 2>&1

echo "Building linux/amd64..."
docker buildx build --platform linux/amd64 --provenance=false --sbom=false \
    -t "${FULL_IMAGE_NAME}:${VERSION}-amd64" --push .
[ $? -ne 0 ] && { echo -e "${RED}Build amd64 failed${NC}"; exit 1; }

echo "Building linux/arm64..."
docker buildx build --platform linux/arm64 --provenance=false --sbom=false \
    -t "${FULL_IMAGE_NAME}:${VERSION}-arm64" --push .
[ $? -ne 0 ] && { echo -e "${RED}Build arm64 failed${NC}"; exit 1; }

sleep 10

echo "Creating manifest (${VERSION} + latest)..."
docker buildx imagetools create \
    -t "${FULL_IMAGE_NAME}:${VERSION}" -t "${FULL_IMAGE_NAME}:latest" \
    "${FULL_IMAGE_NAME}:${VERSION}-amd64" "${FULL_IMAGE_NAME}:${VERSION}-arm64"
[ $? -ne 0 ] && { echo -e "${RED}Manifest failed${NC}"; exit 1; }

echo -e "${GREEN}Done. ${FULL_IMAGE_NAME}:${VERSION} and :latest${NC}"
