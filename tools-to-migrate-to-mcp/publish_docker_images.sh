#!/bin/bash

# Publish Hackerdogs MCP Docker Images to Docker Hub
# This script builds and publishes the MCP server Docker images to public Docker Hub
# under the hackerdogs account.
# Compatible with bash 3.2+ (macOS default)
#
# NOTE: osint-tools is handled separately via:
#   shared/modules/tools/docker/publish_osint_tools.sh
# This separation prevents the large osint-tools build from blocking other images.

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCKER_HUB_USERNAME="hackerdogs"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CONFIG_DIR="${PROJECT_ROOT}/shared/modules/tools/mcp_docker_configs"
PYTHON_SCRIPT="${PROJECT_ROOT}/shared/modules/tools/mcp_docker_client.py"

# Image configurations (using parallel arrays for bash 3.2 compatibility)
# Format: config_name|local_image_name|dockerhub_image_name|build_type|version
# - local_image_name: What Python builds locally
# - dockerhub_image_name: What gets published to Docker Hub (can be different for RSS)
# - version: Version tag (e.g., v1.0.1) - if empty, only uses :latest
#
# NOTE: osint-tools is EXCLUDED from this script because it's a large build (10-15 minutes)
# that blocks other images. Use the dedicated script instead:
#   shared/modules/tools/docker/publish_osint_tools.sh
IMAGE_CONFIGS=(
    "ocr|hackerdogs-mcp-ocr:latest|hackerdogs-mcp-ocr:latest|mcp|"
    "pdf-reader-sylphx|hackerdogs-mcp-pdf-reader-sylphx:latest|hackerdogs-mcp-pdf-reader-sylphx:latest|mcp|"
    "rss|hackerdogs-mcp-rss-mcp:latest|rss-mcp:latest|mcp|"
    "builtwith|hackerdogs-mcp-builtwith:latest|hackerdogs-mcp-builtwith:latest|mcp|"
    "pagespeed|hackerdogs-mcp-pagespeed:latest|hackerdogs-mcp-pagespeed:latest|mcp|"
    "youtube|hackerdogs-mcp-youtube:latest|hackerdogs-mcp-youtube:latest|mcp|"
    "mitre-attack-mcp|hackerdogs-mitre-attack-mcp:latest|hackerdogs-mitre-attack-mcp:latest|dockerfile|"
)

# Function to get local image name from config
get_image_name() {
    local config_name=$1
    local i
    for i in "${IMAGE_CONFIGS[@]}"; do
        local name=$(echo "$i" | cut -d'|' -f1)
        if [ "$name" = "$config_name" ]; then
            echo "$i" | cut -d'|' -f2
            return 0
        fi
    done
    return 1
}

# Function to get Docker Hub image name from config
get_dockerhub_image_name() {
    local config_name=$1
    local i
    for i in "${IMAGE_CONFIGS[@]}"; do
        local name=$(echo "$i" | cut -d'|' -f1)
        if [ "$name" = "$config_name" ]; then
            echo "$i" | cut -d'|' -f3
            return 0
        fi
    done
    return 1
}

# Function to get build type from config
get_build_type() {
    local config_name=$1
    local i
    for i in "${IMAGE_CONFIGS[@]}"; do
        local name=$(echo "$i" | cut -d'|' -f1)
        if [ "$name" = "$config_name" ]; then
            echo "$i" | cut -d'|' -f4
            return 0
        fi
    done
    return 1
}

# Function to get version from config
get_version() {
    local config_name=$1
    local i
    for i in "${IMAGE_CONFIGS[@]}"; do
        local name=$(echo "$i" | cut -d'|' -f1)
        if [ "$name" = "$config_name" ]; then
            echo "$i" | cut -d'|' -f5
            return 0
        fi
    done
    return 1
}

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker ps > /dev/null 2>&1; then
        print_error "Docker is not running or not accessible"
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if logged into Docker Hub
check_docker_login() {
    if ! docker info | grep -q "Username"; then
        print_warning "Not logged into Docker Hub"
        print_info "Please run: docker login"
        read -p "Do you want to login now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
        else
            print_error "Docker Hub login required to push images"
            exit 1
        fi
    fi
    print_success "Logged into Docker Hub"
}

# Function to build Docker image using Python script (for MCP images)
build_mcp_image() {
    local config_name=$1
    local image_name=$2
    local config_file="${CONFIG_DIR}/mcp_${config_name}.json"
    
    if [ ! -f "$config_file" ]; then
        print_error "Config file not found: $config_file"
        return 1
    fi
    
    print_info "Building MCP image for ${config_name}..."
    
    # Use Python to build the image
    python3 -c "
import sys
import json
sys.path.insert(0, '${PROJECT_ROOT}')
from shared.modules.tools.mcp_docker_client import build_mcp_server_docker

with open('${config_file}', 'r') as f:
    config = json.load(f)

result = build_mcp_server_docker(config, force_rebuild=True)
if result:
    print('✅ Image built successfully')
    sys.exit(0)
else:
    print('❌ Failed to build image')
    sys.exit(1)
"
    
    if [ $? -eq 0 ]; then
        print_success "Image built: ${image_name}"
        return 0
    else
        print_error "Failed to build image: ${image_name}"
        return 1
    fi
}

# Function to build Docker image using Dockerfile (for OSINT tools and mitre-attack-mcp)
build_dockerfile_image() {
    local config_name=$1
    local image_name=$2
    local dockerfile_dir=""
    
    # Determine dockerfile directory based on config name
    # NOTE: osint-tools is no longer handled here - use docker/publish_osint_tools.sh instead
    if [ "$config_name" = "mitre-attack-mcp" ]; then
        dockerfile_dir="${PROJECT_ROOT}/mitre-attack-mcp"
    else
        print_error "Unknown dockerfile config: ${config_name}"
        return 1
    fi
    
    if [ ! -f "${dockerfile_dir}/Dockerfile" ]; then
        print_error "Dockerfile not found: ${dockerfile_dir}/Dockerfile"
        return 1
    fi
    
    print_info "Building Dockerfile image: ${image_name}..."
    if [ "$config_name" = "mitre-attack-mcp" ]; then
        print_info "This may take 5-10 minutes..."
    fi
    
    cd "${dockerfile_dir}"
    docker build -t "${image_name}" .
    local build_result=$?
    cd - > /dev/null
    
    if [ $build_result -eq 0 ]; then
        print_success "Image built: ${image_name}"
        return 0
    else
        print_error "Failed to build image: ${image_name}"
        return 1
    fi
}

# Function to build image based on type
build_image() {
    local config_name=$1
    local image_name=$2
    local build_type=$3
    
    if [ "$build_type" = "mcp" ]; then
        build_mcp_image "${config_name}" "${image_name}"
    elif [ "$build_type" = "dockerfile" ]; then
        build_dockerfile_image "${config_name}" "${image_name}"
    else
        print_error "Unknown build type for ${config_name}: ${build_type}"
        return 1
    fi
}

# Function to tag image for Docker Hub
tag_image() {
    local local_image=$1
    local dockerhub_image="${DOCKER_HUB_USERNAME}/${local_image}"
    
    print_info "Tagging ${local_image} as ${dockerhub_image}..."
    docker tag "${local_image}" "${dockerhub_image}"
    
    if [ $? -eq 0 ]; then
        print_success "Tagged: ${dockerhub_image}"
        return 0
    else
        print_error "Failed to tag: ${dockerhub_image}"
        return 1
    fi
}

# Function to push image to Docker Hub
push_image() {
    local dockerhub_image=$1
    
    print_info "Pushing ${dockerhub_image} to Docker Hub..."
    docker push "${dockerhub_image}"
    
    if [ $? -eq 0 ]; then
        print_success "Pushed: ${dockerhub_image}"
        return 0
    else
        print_error "Failed to push: ${dockerhub_image}"
        return 1
    fi
}

# Function to check if local image exists
image_exists_locally() {
    local image_name=$1
    docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${image_name}$"
}

# Function to process a single image
process_image() {
    local config_name=$1
    local local_image_name=$2
    local dockerhub_image_name=$3
    local build_type=$4
    local version=$(get_version "${config_name}")
    
    # Base Docker Hub image name (without tag)
    local dockerhub_base="${DOCKER_HUB_USERNAME}/${dockerhub_image_name%%:*}"
    
    echo ""
    print_info "========================================="
    print_info "Processing: ${config_name}"
    print_info "Local image: ${local_image_name}"
    print_info "Docker Hub base: ${dockerhub_base}"
    if [ -n "${version}" ]; then
        print_info "Version: ${version}"
    fi
    print_info "========================================="
    
    # Step 1: Build image (or verify it exists) - uses local image name
    if image_exists_locally "${local_image_name}"; then
        print_info "Image already exists locally, skipping build"
    else
        if ! build_image "${config_name}" "${local_image_name}" "${build_type}"; then
            print_error "Skipping ${config_name} due to build failure"
            return 1
        fi
    fi
    
    # Verify image exists before tagging
    if ! image_exists_locally "${local_image_name}"; then
        print_error "Image ${local_image_name} does not exist locally after build"
        return 1
    fi
    
    # Step 2: Tag with version (if specified) and latest
    local tags_to_push=()
    
    # Tag with version if specified
    if [ -n "${version}" ]; then
        local versioned_image="${dockerhub_base}:${version}"
        if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${versioned_image}$"; then
            print_info "Version tag already exists, removing old tag..."
            docker rmi "${versioned_image}" 2>/dev/null || true
        fi
        
        print_info "Tagging ${local_image_name} as ${versioned_image}..."
        docker tag "${local_image_name}" "${versioned_image}"
        if [ $? -ne 0 ]; then
            print_error "Failed to tag: ${versioned_image}"
            return 1
        fi
        print_success "Tagged: ${versioned_image}"
        tags_to_push+=("${versioned_image}")
    fi
    
    # Always tag as latest
    local latest_image="${dockerhub_base}:latest"
    if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${latest_image}$"; then
        print_info "Latest tag already exists, removing old tag..."
        docker rmi "${latest_image}" 2>/dev/null || true
    fi
    
    print_info "Tagging ${local_image_name} as ${latest_image}..."
    docker tag "${local_image_name}" "${latest_image}"
    if [ $? -ne 0 ]; then
        print_error "Failed to tag: ${latest_image}"
        return 1
    fi
    print_success "Tagged: ${latest_image}"
    tags_to_push+=("${latest_image}")
    
    # Step 3: Push all tags to Docker Hub
    for tag in "${tags_to_push[@]}"; do
        if ! push_image "${tag}"; then
            print_error "Skipping ${config_name} due to push failure for ${tag}"
            return 1
        fi
    done
    
    print_success "Completed: ${config_name}"
    return 0
}

# Main execution
main() {
    echo ""
    print_info "========================================="
    print_info "Hackerdogs MCP Docker Images Publisher"
    print_info "========================================="
    echo ""
    
    # Check prerequisites
    check_docker
    check_docker_login
    
    # Verify we're in the right directory
    if [ ! -f "${PYTHON_SCRIPT}" ]; then
        print_error "Python script not found: ${PYTHON_SCRIPT}"
        print_error "Please run this script from the project root"
        exit 1
    fi
    
    # Count images and list them
    local total_images=${#IMAGE_CONFIGS[@]}
    print_info "Found ${total_images} Docker image(s) to publish:"
    local i
    for i in "${IMAGE_CONFIGS[@]}"; do
        local local_image=$(echo "$i" | cut -d'|' -f2)
        local dockerhub_image=$(echo "$i" | cut -d'|' -f3)
        echo "  - ${local_image} → ${DOCKER_HUB_USERNAME}/${dockerhub_image}"
    done
    echo ""
    
    # Process each image
    local success_count=0
    local fail_count=0
    
    for i in "${IMAGE_CONFIGS[@]}"; do
        local config_name=$(echo "$i" | cut -d'|' -f1)
        local local_image_name=$(echo "$i" | cut -d'|' -f2)
        local dockerhub_image_name=$(echo "$i" | cut -d'|' -f3)
        local build_type=$(echo "$i" | cut -d'|' -f4)
        
        if process_image "${config_name}" "${local_image_name}" "${dockerhub_image_name}" "${build_type}"; then
            success_count=$((success_count + 1))
        else
            fail_count=$((fail_count + 1))
        fi
    done
    
    # Summary
    echo ""
    print_info "========================================="
    print_info "Summary"
    print_info "========================================="
    print_info "Total images: ${total_images}"
    print_success "Successfully published: ${success_count}"
    if [ ${fail_count} -gt 0 ]; then
        print_error "Failed: ${fail_count}"
    fi
    echo ""
    
    if [ ${fail_count} -eq 0 ]; then
        print_success "All images published successfully! 🎉"
        echo ""
        print_info "Published images:"
        for i in "${IMAGE_CONFIGS[@]}"; do
            local dockerhub_image_name=$(echo "$i" | cut -d'|' -f3)
            echo "  - ${DOCKER_HUB_USERNAME}/${dockerhub_image_name}"
        done
        exit 0
    else
        print_error "Some images failed to publish"
        exit 1
    fi
}

# Run main function
main "$@"
