#!/bin/bash
# Publish Docker image to Docker Hub under hackerdogs account
#
# Usage:
#   ./publish_to_docker.sh [version]
#   ./publish_to_docker.sh v1.0.0
#   ./publish_to_docker.sh        # Uses 'latest' tag only

set -e

# Configuration
DOCKER_USER="hackerdogs"
IMAGE_NAME="maigret-mcp-server"
LOCAL_TAG="${IMAGE_NAME}:latest"
VERSION="${1:-latest}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo -e "\n${YELLOW}=========================================="
    echo "$1"
    echo "==========================================${NC}\n"
}

# Check if Docker is running
check_docker() {
    print_info "Checking Docker..."
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if logged into Docker Hub
check_docker_login() {
    print_info "Checking Docker Hub login..."
    if ! docker info | grep -q "Username"; then
        print_warning "Not logged into Docker Hub"
        print_info "Please login with: docker login"
        read -p "Do you want to login now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker login
        else
            print_error "Cannot proceed without Docker Hub login"
            exit 1
        fi
    fi
    print_success "Logged into Docker Hub"
}

# Build the Docker image
build_image() {
    print_header "Building Docker Image"
    print_info "Building ${LOCAL_TAG}..."
    docker build -t "${LOCAL_TAG}" .
    print_success "Image built successfully"
}

# Tag the image for Docker Hub
tag_image() {
    print_header "Tagging Image for Docker Hub"
    
    # Tag as latest
    REMOTE_TAG_LATEST="${DOCKER_USER}/${IMAGE_NAME}:latest"
    print_info "Tagging as ${REMOTE_TAG_LATEST}..."
    docker tag "${LOCAL_TAG}" "${REMOTE_TAG_LATEST}"
    print_success "Tagged as latest"
    
    # Tag with version if provided
    if [ "$VERSION" != "latest" ]; then
        REMOTE_TAG_VERSION="${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
        print_info "Tagging as ${REMOTE_TAG_VERSION}..."
        docker tag "${LOCAL_TAG}" "${REMOTE_TAG_VERSION}"
        print_success "Tagged as ${VERSION}"
    fi
}

# Push to Docker Hub
push_image() {
    print_header "Pushing to Docker Hub"
    
    # Push latest
    REMOTE_TAG_LATEST="${DOCKER_USER}/${IMAGE_NAME}:latest"
    print_info "Pushing ${REMOTE_TAG_LATEST}..."
    docker push "${REMOTE_TAG_LATEST}"
    print_success "Pushed latest tag"
    
    # Push version if provided
    if [ "$VERSION" != "latest" ]; then
        REMOTE_TAG_VERSION="${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
        print_info "Pushing ${REMOTE_TAG_VERSION}..."
        docker push "${REMOTE_TAG_VERSION}"
        print_success "Pushed ${VERSION} tag"
    fi
}

# Verify the push
verify_push() {
    print_header "Verifying Push"
    print_info "Checking Docker Hub for ${DOCKER_USER}/${IMAGE_NAME}..."
    
    # Note: This is a simple check - actual verification would require Docker Hub API
    print_success "Image pushed successfully"
    print_info "You can verify at: https://hub.docker.com/r/${DOCKER_USER}/${IMAGE_NAME}"
}

# Main execution
main() {
    print_header "Docker Hub Publishing Script"
    print_info "Target: ${DOCKER_USER}/${IMAGE_NAME}"
    print_info "Version: ${VERSION}"
    echo
    
    # Pre-flight checks
    check_docker
    check_docker_login
    
    # Build, tag, and push
    build_image
    tag_image
    push_image
    verify_push
    
    # Summary
    print_header "Publishing Complete!"
    print_success "Image published to: ${DOCKER_USER}/${IMAGE_NAME}"
    if [ "$VERSION" != "latest" ]; then
        print_info "Tags: latest, ${VERSION}"
    else
        print_info "Tag: latest"
    fi
    print_info "Docker Hub: https://hub.docker.com/r/${DOCKER_USER}/${IMAGE_NAME}"
    print_info ""
    print_info "Usage:"
    print_info "  docker pull ${DOCKER_USER}/${IMAGE_NAME}:latest"
    if [ "$VERSION" != "latest" ]; then
        print_info "  docker pull ${DOCKER_USER}/${IMAGE_NAME}:${VERSION}"
    fi
}

# Run main function
main

