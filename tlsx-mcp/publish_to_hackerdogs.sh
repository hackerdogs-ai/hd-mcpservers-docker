#!/bin/bash
# Build and Publish TLSx MCP Docker Image to Docker Hub

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="tlsx-mcp"
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

# Show help if requested or no flags set
if [ "$SHOW_HELP" = true ]; then
    echo "Build and Publish TLSx MCP Docker Image to Docker Hub"
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
    echo "  $0 hackerdogs                              # Build and publish with tag 'latest'"
    echo "  $0 --build hackerdogs                      # Only build (tag: latest)"
    echo "  $0 --publish hackerdogs                    # Only publish"
    echo "  $0 --build --publish hackerdogs v1.0.0     # Build and publish with tag v1.0.0"
    echo "  $0 --build --publish --platforms sequential hackerdogs latest"
    exit 0
fi

# If neither flag is set, do both (default behavior)
if [ "$DO_BUILD" = false ] && [ "$DO_PUBLISH" = false ]; then
    DO_BUILD=true
    DO_PUBLISH=true
fi

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

# Get tags
TAGS=("${ARGS[@]:1}")
if [ ${#TAGS[@]} -eq 0 ]; then
    TAGS=("$DEFAULT_TAG")
fi

# Display operation summary
echo "================================================================================="
if [ "$DO_BUILD" = true ] && [ "$DO_PUBLISH" = true ]; then
    echo -e "${BLUE}Building and Publishing TLSx MCP Docker Image${NC}"
elif [ "$DO_BUILD" = true ]; then
    echo -e "${BLUE}Building TLSx MCP Docker Image${NC}"
else
    echo -e "${BLUE}Publishing TLSx MCP Docker Image to Docker Hub${NC}"
fi
echo "================================================================================="
if [ "$DO_PUBLISH" = true ]; then
    echo "Docker Hub Username: ${GREEN}${DOCKERHUB_USERNAME}${NC}"
fi
echo "Image Name: ${GREEN}${IMAGE_NAME}${NC}"
if [ "$DO_BUILD" = true ]; then
    echo "Dockerfile: ${GREEN}${DOCKERFILE}${NC}"
fi
echo "Tags: ${GREEN}${TAGS[*]}${NC}"
echo "Full Image Name: ${GREEN}${FULL_IMAGE_NAME}${NC}"
echo "================================================================================="
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running or not accessible${NC}"
    exit 1
fi

# Setup Docker Buildx
echo -e "${YELLOW}Setting up Docker Buildx for multi-platform support...${NC}"
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker Buildx is not available${NC}"
    exit 1
fi

BUILDER_NAME="multiarch-builder"
if ! docker buildx inspect "$BUILDER_NAME" > /dev/null 2>&1; then
    echo -e "${YELLOW}Creating multi-platform builder: ${BUILDER_NAME}${NC}"
    docker buildx create --name "$BUILDER_NAME" --use --bootstrap
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create buildx builder${NC}"
        exit 1
    fi
else
    docker buildx use "$BUILDER_NAME" > /dev/null 2>&1
fi
echo -e "${GREEN}✅ Buildx builder ready${NC}"
echo ""

# Check Docker Hub auth
if [ "$DO_PUBLISH" = true ]; then
    echo -e "${YELLOW}Checking Docker Hub authentication...${NC}"
    if ! docker info | grep -q "Username"; then
        echo -e "${YELLOW}You are not logged in to Docker Hub.${NC}"
        read -p "Do you want to log in now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
            if [ $? -ne 0 ]; then
                echo -e "${RED}Error: Docker login failed${NC}"
                exit 1
            fi
        else
            echo -e "${RED}Error: Docker Hub login required for publishing${NC}"
            exit 1
        fi
    else
        echo -e "${GREEN}✅ Docker Hub authentication verified${NC}"
    fi
    echo ""
fi

# Build
if [ "$DO_BUILD" = true ]; then
    if [ ! -f "$DOCKERFILE" ]; then
        echo -e "${RED}Error: Dockerfile not found: ${DOCKERFILE}${NC}"
        exit 1
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

    if [ "$DO_PUBLISH" = true ]; then
        echo -e "${YELLOW}Building Docker image from ${DOCKERFILE} (multi-platform)...${NC}"
        echo "Platforms: linux/amd64, linux/arm64"
        echo ""

        for tag in "${TAGS[@]}"; do
            if [ "$PLATFORMS_MODE" = "sequential" ]; then
                echo "Building and pushing ${FULL_IMAGE_NAME}:${tag} (sequential)..."
                if ! do_build_push_with_retry docker buildx build \
                    --platform linux/amd64 \
                    --provenance=false \
                    --sbom=false \
                    -f "$DOCKERFILE" \
                    -t "${FULL_IMAGE_NAME}:${tag}-amd64" \
                    --push \
                    . ; then
                    echo -e "${RED}Error: Failed to build/push amd64 after $MAX_RETRIES attempts${NC}"
                    exit 1
                fi
                echo -e "${GREEN}✅ Pushed ${FULL_IMAGE_NAME}:${tag}-amd64${NC}"

                if ! do_build_push_with_retry docker buildx build \
                    --platform linux/arm64 \
                    --provenance=false \
                    --sbom=false \
                    -f "$DOCKERFILE" \
                    -t "${FULL_IMAGE_NAME}:${tag}-arm64" \
                    --push \
                    . ; then
                    echo -e "${RED}Error: Failed to build/push arm64 after $MAX_RETRIES attempts${NC}"
                    exit 1
                fi
                echo -e "${GREEN}✅ Pushed ${FULL_IMAGE_NAME}:${tag}-arm64${NC}"

                docker buildx imagetools create -t "${FULL_IMAGE_NAME}:${tag}" \
                    "${FULL_IMAGE_NAME}:${tag}-amd64" \
                    "${FULL_IMAGE_NAME}:${tag}-arm64"
                if [ $? -ne 0 ]; then
                    echo -e "${RED}Error: Failed to create manifest for ${FULL_IMAGE_NAME}:${tag}${NC}"
                    exit 1
                fi
            else
                echo "Building and pushing ${FULL_IMAGE_NAME}:${tag}..."
                if ! do_build_push_with_retry docker buildx build \
                    --platform linux/amd64,linux/arm64 \
                    --provenance=false \
                    --sbom=false \
                    -f "$DOCKERFILE" \
                    -t "${FULL_IMAGE_NAME}:${tag}" \
                    --push \
                    . ; then
                    echo -e "${RED}Error: Docker buildx build failed after $MAX_RETRIES attempts${NC}"
                    exit 1
                fi
            fi
            echo -e "${GREEN}✅ Successfully built and pushed ${FULL_IMAGE_NAME}:${tag} (multi-platform)${NC}"
        done
    else
        echo -e "${YELLOW}Building Docker image from ${DOCKERFILE} (local platform only)...${NC}"
        echo ""

        LOCAL_IMAGE_NAME="${IMAGE_NAME}:${TAGS[0]}"
        docker buildx build \
            --load \
            -f "$DOCKERFILE" \
            -t "${LOCAL_IMAGE_NAME}" \
            .

        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Docker build failed${NC}"
            exit 1
        fi

        echo -e "${GREEN}✅ Docker image built successfully (local: ${LOCAL_IMAGE_NAME})${NC}"

        REGISTRY_TAG="hackerdogs/${IMAGE_NAME}:${TAGS[0]}"
        echo ""
        echo -e "${YELLOW}Tagging image for docker-compose compatibility: ${REGISTRY_TAG}${NC}"
        docker tag "${LOCAL_IMAGE_NAME}" "${REGISTRY_TAG}"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✅ Tagged as ${REGISTRY_TAG} (for docker-compose)${NC}"
        else
            echo -e "${YELLOW}Warning: Failed to tag image for docker-compose${NC}"
        fi

        if [ ${#TAGS[@]} -gt 1 ]; then
            echo ""
            echo -e "${YELLOW}Tagging image with additional tags...${NC}"
            for tag in "${TAGS[@]:1}"; do
                docker tag "${LOCAL_IMAGE_NAME}" "${IMAGE_NAME}:${tag}"
                docker tag "${LOCAL_IMAGE_NAME}" "hackerdogs/${IMAGE_NAME}:${tag}"
            done
            echo -e "${GREEN}✅ All tags created${NC}"
        fi
    fi
fi

# Publish only (no build)
if [ "$DO_PUBLISH" = true ] && [ "$DO_BUILD" = false ]; then
    echo ""
    echo -e "${YELLOW}Pushing remaining images...${NC}"
    for tag in "${TAGS[@]}"; do
        echo "Pushing ${FULL_IMAGE_NAME}:${tag}..."
        docker push "${FULL_IMAGE_NAME}:${tag}"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Error: Failed to push ${FULL_IMAGE_NAME}:${tag}${NC}"
            exit 1
        fi
        echo -e "${GREEN}✅ Successfully pushed ${FULL_IMAGE_NAME}:${tag}${NC}"
    done
fi

# Summary
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
echo ""
echo "Image: ${GREEN}${FULL_IMAGE_NAME}:${TAGS[0]}${NC}"
if [ "$DO_PUBLISH" = true ] && [ "$DO_BUILD" = true ]; then
    echo "Platforms: ${GREEN}linux/amd64, linux/arm64${NC} (multi-platform)"
fi

VERSION_FILE="${IMAGE_NAME}_versions.txt"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TAGS_CSV=$(IFS=','; echo "${TAGS[*]}")

if [ "$DO_PUBLISH" = true ]; then
    PLATFORMS="linux/amd64,linux/arm64"
    DOCKERHUB_LINK="https://hub.docker.com/r/${DOCKERHUB_USERNAME}/${IMAGE_NAME}/tags"
    VERSION_LINE="${TAGS_CSV},${PLATFORMS},${TIMESTAMP},${DOCKERHUB_LINK}"
    echo "$VERSION_LINE" >> "$VERSION_FILE"
    echo ""
    echo "Version Tags: ${GREEN}${TAGS[*]}${NC}"
    echo "Version info saved to: ${GREEN}${VERSION_FILE}${NC}"
elif [ "$DO_BUILD" = true ]; then
    VERSION_LINE="${TAGS_CSV},local,${TIMESTAMP},local"
    echo "$VERSION_LINE" >> "$VERSION_FILE"
    echo ""
    echo "Version Tags: ${GREEN}${TAGS[*]}${NC}"
    echo "Version info saved to: ${GREEN}${VERSION_FILE}${NC}"
fi
echo ""
