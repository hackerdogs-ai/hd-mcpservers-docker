#!/bin/bash
# Build and Publish MCP Farm Auth-Gateway Docker Image to Docker Hub
# Image name: auth-gateway

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

IMAGE_NAME="auth-gateway"
DOCKERFILE="Dockerfile"
DEFAULT_TAG="latest"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DO_BUILD=false
DO_PUBLISH=false
SHOW_HELP=false
PLATFORMS_MODE="parallel"

ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)    DO_BUILD=true; shift ;;
        --publish)  DO_PUBLISH=true; shift ;;
        --platforms) PLATFORMS_MODE="$2"; shift 2 ;;
        --help|-h)  SHOW_HELP=true; shift ;;
        *)          ARGS+=("$1"); shift ;;
    esac
done

if [ "$SHOW_HELP" = true ]; then
    echo "Build and Publish MCP Farm Auth-Gateway Docker Image to Docker Hub"
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
    exit 0
fi

if [ "$DO_BUILD" = false ] && [ "$DO_PUBLISH" = false ]; then
    DO_BUILD=true
    DO_PUBLISH=true
fi

if [ "$PLATFORMS_MODE" != "sequential" ]; then
    PLATFORMS_MODE="parallel"
fi

cd "$PROJECT_ROOT"

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
    echo -e "${BLUE}Building and Publishing MCP Farm Auth-Gateway Docker Image${NC}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${BLUE}Building MCP Farm Auth-Gateway Docker Image${NC}"
else
    echo -e "${BLUE}Publishing MCP Farm Auth-Gateway Docker Image to Docker Hub${NC}"
fi
echo "================================================================================="
if [ "$DO_PUBLISH" = true ]; then
    echo "Docker Hub Username: ${GREEN}${DOCKERHUB_USERNAME}${NC}"
fi
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
else
    docker buildx use "$BUILDER_NAME" > /dev/null 2>&1
fi
echo -e "${GREEN}Buildx builder ready${NC}"
echo ""

if [ "$DO_PUBLISH" = true ]; then
    echo -e "${YELLOW}Checking Docker Hub authentication...${NC}"
    if ! docker info | grep -q "Username"; then
        echo -e "${YELLOW}You are not logged in to Docker Hub.${NC}"
        read -p "Do you want to log in now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login || { echo -e "${RED}Error: Docker login failed${NC}"; exit 1; }
        else
            echo -e "${RED}Error: Docker Hub login required for publishing${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}Docker Hub authentication verified${NC}"
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
        if "$@"; then return 0; fi
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
        echo -e "${YELLOW}Building Docker image from ${DOCKERFILE} (multi-platform)...${NC}"
        for tag in "${TAGS[@]}"; do
            if [ "$PLATFORMS_MODE" = "sequential" ]; then
                do_build_push_with_retry docker buildx build --platform linux/amd64 --provenance=false --sbom=false -f "$DOCKERFILE" -t "${FULL_IMAGE_NAME}:${tag}-amd64" --push . || exit 1
                do_build_push_with_retry docker buildx build --platform linux/arm64 --provenance=false --sbom=false -f "$DOCKERFILE" -t "${FULL_IMAGE_NAME}:${tag}-arm64" --push . || exit 1
                docker buildx imagetools create -t "${FULL_IMAGE_NAME}:${tag}" "${FULL_IMAGE_NAME}:${tag}-amd64" "${FULL_IMAGE_NAME}:${tag}-arm64" || exit 1
            else
                do_build_push_with_retry docker buildx build --platform linux/amd64,linux/arm64 --provenance=false --sbom=false -f "$DOCKERFILE" -t "${FULL_IMAGE_NAME}:${tag}" --push . || exit 1
            fi
            echo -e "${GREEN}Successfully built and pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
        done
    else
        echo -e "${YELLOW}Building Docker image from ${DOCKERFILE} (local platform only)...${NC}"
        LOCAL_IMAGE_NAME="${IMAGE_NAME}:${TAGS[0]}"
        docker buildx build --load -f "$DOCKERFILE" -t "${LOCAL_IMAGE_NAME}" . || exit 1
        echo -e "${GREEN}Docker image built successfully (local: ${LOCAL_IMAGE_NAME})${NC}"
        REGISTRY_TAG="hackerdogs/${IMAGE_NAME}:${TAGS[0]}"
        docker tag "${LOCAL_IMAGE_NAME}" "${REGISTRY_TAG}"
        echo -e "${GREEN}Tagged as ${REGISTRY_TAG} (for docker-compose)${NC}"
    fi
fi

if [ "$DO_PUBLISH" = true ] && [ "$DO_BUILD" = false ]; then
    echo -e "${YELLOW}Pushing images...${NC}"
    for tag in "${TAGS[@]}"; do
        docker push "${FULL_IMAGE_NAME}:${tag}" || { echo -e "${RED}Error: Failed to push ${FULL_IMAGE_NAME}:${tag}${NC}"; exit 1; }
        echo -e "${GREEN}Successfully pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
    done
fi

echo ""
echo "================================================================================="
echo -e "${GREEN}Done!${NC}"
echo "================================================================================="
echo "Image: ${GREEN}${FULL_IMAGE_NAME}:${TAGS[0]}${NC}"
