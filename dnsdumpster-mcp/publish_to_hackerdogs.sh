#!/bin/bash
# ============================================================
# publish_to_hackerdogs.sh - Build and Publish dnsdumpster-mcp
# ============================================================
#
# Build (and optionally publish) multi-arch Docker images for
# the dnsdumpster MCP server.
#
# Usage:
#   ./publish_to_hackerdogs.sh [--build] [--publish] [--platforms linux/amd64,linux/arm64] [--help]
#
# Flags:
#   --build      Build the image (default if no flags specified)
#   --publish    Push image to Docker Hub
#   --platforms  Comma-separated platforms (default: linux/amd64,linux/arm64)
#   --help       Show usage information
#
# If no flags are specified, both --build and --publish are assumed.

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
IMAGE_NAME="hackerdogs/dnsdumpster-mcp"
DOCKERFILE="Dockerfile"
CONTEXT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Defaults
DO_BUILD=false
DO_PUBLISH=false
PLATFORMS="linux/amd64,linux/arm64"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)   DO_BUILD=true;  shift ;;
        --publish) DO_PUBLISH=true; shift ;;
        --platforms) PLATFORMS="$2"; shift 2 ;;
        --help)
            echo "Usage: $0 [--build] [--publish] [--platforms <platforms>]"
            exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; exit 1 ;;
    esac
done

# Default: both build and publish
if ! $DO_BUILD && ! $DO_PUBLISH; then
    DO_BUILD=true
    DO_PUBLISH=true
fi

# Docker Hub username (required for publish)
DOCKER_USER="${DOCKER_USERNAME:-hackerdogs}"
TAG="latest"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} dnsdumpster-mcp - Build & Publish${NC}"
echo -e "${GREEN}========================================${NC}"
echo "Image:     ${IMAGE_NAME}:${TAG}"
echo "Platforms: ${PLATFORMS}"
echo "Build:     ${DO_BUILD}"
echo "Publish:   ${DO_PUBLISH}"
echo ""

# Check Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: docker not found${NC}"
    exit 1
fi

# Ensure buildx is available
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}Error: docker buildx not available${NC}"
    exit 1
fi

# Create/use multi-arch builder
BUILDER_NAME="multiarch-builder"
if ! docker buildx inspect "$BUILDER_NAME" &> /dev/null; then
    echo "Creating buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --use
else
    docker buildx use "$BUILDER_NAME"
fi

# Check Docker Hub auth if publishing
if $DO_PUBLISH; then
    if ! docker info 2>/dev/null | grep -q "Username"; then
        echo -e "${YELLOW}Warning: Not logged in to Docker Hub. Run 'docker login' first.${NC}"
    fi
fi

do_build_push_with_retry() {
    local max_retries=3
    local attempt=1
    local push_flag=""
    $DO_PUBLISH && push_flag="--push"

    while [ $attempt -le $max_retries ]; do
        echo -e "\n${GREEN}Build attempt $attempt/$max_retries${NC}"
        if docker buildx build \
            --platform "$PLATFORMS" \
            -t "${IMAGE_NAME}:${TAG}" \
            -f "${CONTEXT_DIR}/${DOCKERFILE}" \
            $push_flag \
            "$CONTEXT_DIR"; then
            echo -e "${GREEN}Build succeeded!${NC}"
            return 0
        fi
        echo -e "${YELLOW}Attempt $attempt failed, retrying...${NC}"
        attempt=$((attempt + 1))
        sleep 5
    done

    echo -e "${RED}Build failed after $max_retries attempts${NC}"
    return 1
}

if $DO_BUILD; then
    do_build_push_with_retry
fi

# Record version info
VERSION_FILE="${CONTEXT_DIR}/${IMAGE_NAME##*/}_versions.txt"
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | ${IMAGE_NAME}:${TAG} | platforms=${PLATFORMS}" >> "$VERSION_FILE" 2>/dev/null || true

echo -e "\n${GREEN}Done!${NC}"
