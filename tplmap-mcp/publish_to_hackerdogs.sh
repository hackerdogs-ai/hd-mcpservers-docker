#!/bin/bash
# Build and Publish Tplmap MCP Server Docker Image to Docker Hub
# Image name: tplmap-mcp

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="tplmap-mcp"
DOCKERFILE="Dockerfile"
DEFAULT_TAG="latest"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Flags
DO_BUILD=false
DO_PUBLISH=false
SHOW_HELP=false
PLATFORMS_MODE="parallel"

# Parse command-line arguments
ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            DO_BUILD=true
            shift
            ;;
        --publish)
            DO_PUBLISH=true
            shift
            ;;
        --platforms)
            PLATFORMS_MODE="$2"
            shift 2
            ;;
        --help|-h)
            SHOW_HELP=true
            shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

# Show help if requested
if [ "$SHOW_HELP" = true ]; then
    echo "Build and Publish Tplmap MCP Server Docker Image to Docker Hub"
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS] <dockerhub_username> [tag] [additional_tag...]"
    echo ""
    echo "Options:"
    echo "  --build      Only build the Docker image (do not publish)"
    echo "  --publish    Only publish the Docker image (assumes image already exists)"
    echo "  --platforms parallel|sequential  Push both platforms at once (default) or amd64 then arm64"
    echo "  --help, -h   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 hackerdogs                    # Build and publish with tag 'latest'"
    echo "  $0 --build hackerdogs             # Only build (tag: latest)"
    echo "  $0 --publish hackerdogs           # Only publish"
    echo "  $0 --build --publish hackerdogs v1.0.0           # Build and publish with tag v1.0.0"
    echo "  $0 --build --publish --platforms sequential hackerdogs v1.0.0 latest"
    exit 0
fi

# If neither flag is set, do both (default behavior)
if [ "$DO_BUILD" = false ] && [ "$DO_PUBLISH" = false ]; then
    DO_BUILD=true
    DO_PUBLISH=true
fi

# Normalize platforms mode
if [ "$PLATFORMS_MODE" != "sequential" ]; then
    PLATFORMS_MODE="parallel"
fi

cd "$PROJECT_ROOT"

# Get Docker Hub username
if [ "$DO_PUBLISH" = true ]; then
    if [ ${#ARGS[@]} -eq 0 ]; then
        echo -e "${YELLOW}Docker Hub username not provided.${NC}"
        read -p "Enter your Docker Hub username: " DOCKERHUB_USERNAME
        if [ -z "$DOCKERHUB_USERNAME" ]; then
            echo -e "${RED}Error: Docker Hub username is required for publishing${NC}"
            exit 1
        fi
    else
        DOCKERHUB_USERNAME="${ARGS[0]}"
    fi
    FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}"
else
    DOCKERHUB_USERNAME=""
    FULL_IMAGE_NAME="${IMAGE_NAME}"
fi

TAGS=("${ARGS[@]:1}")
if [ ${#TAGS[@]} -eq 0 ]; then
    TAGS=("$DEFAULT_TAG")
fi

echo "================================================================================="
if [ "$DO_BUILD" = true ] && [ "$DO_PUBLISH" = true ]; then
    echo -e "${BLUE}Building and Publishing Tplmap MCP Server Docker Image${NC}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${BLUE}Building Tplmap MCP Server Docker Image${NC}"
else
    echo -e "${BLUE}Publishing Tplmap MCP Server Docker Image to Docker Hub${NC}"
fi
echo "================================================================================="
[ "$DO_PUBLISH" = true ] && echo "Docker Hub Username: ${GREEN}${DOCKERHUB_USERNAME}${NC}"
echo "Image Name: ${GREEN}${IMAGE_NAME}${NC}"
echo "Tags: ${GREEN}${TAGS[*]}${NC}"
echo "Full Image Name: ${GREEN}${FULL_IMAGE_NAME}${NC}"
echo "================================================================================="
echo ""

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running or not accessible${NC}"
    exit 1
fi

echo -e "${YELLOW}Setting up Docker Buildx for multi-platform support...${NC}"
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker Buildx is not available. Please upgrade Docker.${NC}"
    exit 1
fi

BUILDER_NAME="multiarch-builder"
if ! docker buildx inspect "$BUILDER_NAME" > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating multi-platform builder: ${BUILDER_NAME}${NC}"
    docker buildx create --name "$BUILDER_NAME" --use --bootstrap
    [ $? -ne 0 ] && echo -e "${RED}Error: Failed to create buildx builder${NC}" && exit 1
else
    docker buildx use "$BUILDER_NAME" > /dev/null 2>&1
fi
echo -e "${GREEN}✅ Buildx builder ready${NC}"
echo ""

if [ "$DO_PUBLISH" = true ]; then
    echo -e "${YELLOW}Checking Docker Hub authentication...${NC}"
    if ! docker info | grep -q "Username"; then
        echo -e "${YELLOW}You are not logged in to Docker Hub.${NC}"
        echo "Please log in with: docker login"
        read -p "Do you want to log in now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
            [ $? -ne 0 ] && echo -e "${RED}Error: Docker login failed${NC}" && exit 1
        else
            echo -e "${RED}Error: Docker Hub login required for publishing${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Docker Hub authentication verified${NC}"
    fi
    echo ""
fi

MAX_RETRIES=5
do_build_push_with_retry() {
    local retry=0
    local backoff=30
    while [ $retry -lt $MAX_RETRIES ]; do
        if [ $retry -gt 0 ]; then
            echo -e "${YELLOW}Retry $retry/$MAX_RETRIES in ${backoff}s...${NC}"
            sleep "$backoff"
            backoff=$((backoff * 2))
            [ $backoff -gt 300 ] && backoff=300
        fi
        if "$@"; then
            return 0
        fi
        retry=$((retry + 1))
    done
    return 1
}

if [ "$DO_BUILD" = true ]; then
    if [ ! -f "$DOCKERFILE" ]; then
        echo -e "${RED}Error: Dockerfile not found: ${DOCKERFILE}${NC}"
        exit 1
    fi

    if [ "$DO_PUBLISH" = true ]; then
        echo -e "${YELLOW}Building Docker image (multi-platform)...${NC}"
        for tag in "${TAGS[@]}"; do
            if [ "$PLATFORMS_MODE" = "sequential" ]; then
                for arch in amd64 arm64; do
                    echo "Building ${FULL_IMAGE_NAME}:${tag}-${arch}..."
                    if ! do_build_push_with_retry docker buildx build \
                        --platform linux/$arch \
                        --provenance=false --sbom=false \
                        -f "$DOCKERFILE" -t "${FULL_IMAGE_NAME}:${tag}-${arch}" \
                        --push . ; then
                        echo -e "${RED}Error: Failed to build/push $arch after $MAX_RETRIES attempts${NC}"
                        exit 1
                    fi
                    echo -e "${GREEN}✅ Pushed ${FULL_IMAGE_NAME}:${tag}-${arch}${NC}"
                done
                docker buildx imagetools create -t "${FULL_IMAGE_NAME}:${tag}" \
                    "${FULL_IMAGE_NAME}:${tag}-amd64" "${FULL_IMAGE_NAME}:${tag}-arm64"
                [ $? -ne 0 ] && echo -e "${RED}Error: Failed to create manifest${NC}" && exit 1
            else
                echo "Building ${FULL_IMAGE_NAME}:${tag}..."
                if ! do_build_push_with_retry docker buildx build \
                    --platform linux/amd64,linux/arm64 \
                    --provenance=false --sbom=false \
                    -f "$DOCKERFILE" -t "${FULL_IMAGE_NAME}:${tag}" \
                    --push . ; then
                    echo -e "${RED}Error: Build failed after $MAX_RETRIES attempts${NC}"
                    exit 1
                fi
            fi
            echo -e "${GREEN}✅ Successfully built and pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
        done
    else
        echo -e "${YELLOW}Building Docker image (local platform only)...${NC}"
        LOCAL_IMAGE_NAME="${IMAGE_NAME}:${TAGS[0]}"
        docker buildx build --load -f "$DOCKERFILE" -t "${LOCAL_IMAGE_NAME}" .
        [ $? -ne 0 ] && echo -e "${RED}Error: Docker build failed${NC}" && exit 1
        echo -e "${GREEN}✅ Docker image built: ${LOCAL_IMAGE_NAME}${NC}"

        REGISTRY_TAG="hackerdogs/${IMAGE_NAME}:${TAGS[0]}"
        docker tag "${LOCAL_IMAGE_NAME}" "${REGISTRY_TAG}"
        echo -e "${GREEN}✅ Tagged as ${REGISTRY_TAG}${NC}"
    fi
fi

if [ "$DO_PUBLISH" = true ] && [ "$DO_BUILD" = false ]; then
    for tag in "${TAGS[@]}"; do
        echo "Pushing ${FULL_IMAGE_NAME}:${tag}..."
        docker push "${FULL_IMAGE_NAME}:${tag}"
        [ $? -ne 0 ] && echo -e "${RED}Error: Failed to push${NC}" && exit 1
        echo -e "${GREEN}✅ Pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
    done
fi

echo ""
echo "================================================================================="
if [ "$DO_BUILD" = true ] && [ "$DO_PUBLISH" = true ]; then
    echo -e "${GREEN}✅ Build and Publish Complete!${NC}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${GREEN}✅ Build Complete!${NC}"
else
    echo -e "${GREEN}✅ Publish Complete!${NC}"
fi
echo "================================================================================="
echo "Image: ${GREEN}${FULL_IMAGE_NAME}:${TAGS[0]}${NC}"

VERSION_FILE="${IMAGE_NAME}_versions.txt"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TAGS_CSV=$(IFS=','; echo "${TAGS[*]}")
if [ "$DO_PUBLISH" = true ]; then
    echo "${TAGS_CSV},linux/amd64+linux/arm64,${TIMESTAMP},https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}/tags" >> "$VERSION_FILE"
elif [ "$DO_BUILD" = true ]; then
    echo "${TAGS_CSV},local,${TIMESTAMP},local" >> "$VERSION_FILE"
fi
echo "Version info saved to: ${GREEN}${VERSION_FILE}${NC}"
echo ""
