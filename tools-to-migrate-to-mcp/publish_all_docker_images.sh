#!/bin/bash

# Master script to publish all Docker images (MCP servers + osint-tools)
# This script coordinates building both the fast MCP images and the large osint-tools image
# Compatible with bash 3.2+ (macOS default)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

# Paths
MCP_PUBLISH_SCRIPT="${SCRIPT_DIR}/publish_docker_images.sh"
OSINT_PUBLISH_SCRIPT="${SCRIPT_DIR}/docker/publish_osint_tools.sh"

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

# Function to check if script exists
check_script() {
    local script_path=$1
    if [ ! -f "$script_path" ]; then
        print_error "Script not found: $script_path"
        return 1
    fi
    if [ ! -x "$script_path" ]; then
        print_warning "Script not executable, making it executable..."
        chmod +x "$script_path"
    fi
    return 0
}

# Main execution
main() {
    echo ""
    print_info "========================================="
    print_info "Hackerdogs Docker Images Publisher"
    print_info "Master Script - All Images"
    print_info "========================================="
    echo ""
    
    # Check if scripts exist
    if ! check_script "$MCP_PUBLISH_SCRIPT"; then
        exit 1
    fi
    
    if ! check_script "$OSINT_PUBLISH_SCRIPT"; then
        exit 1
    fi
    
    # Check Docker Hub username
    DOCKER_HUB_USERNAME="${1:-hackerdogs}"
    print_info "Docker Hub Username: ${DOCKER_HUB_USERNAME}"
    echo ""
    
    # Ask user what to build
    print_info "What would you like to build?"
    echo "  1) MCP images only (fast, ~2-5 minutes)"
    echo "  2) osint-tools only (slow, ~10-15 minutes)"
    echo "  3) All images (MCP first, then osint-tools)"
    echo "  4) Cancel"
    echo ""
    read -p "Enter choice [1-4]: " choice
    
    case "$choice" in
        1)
            print_info "Building MCP images only..."
            echo ""
            bash "$MCP_PUBLISH_SCRIPT"
            ;;
        2)
            print_info "Building osint-tools only..."
            echo ""
            cd "${SCRIPT_DIR}/docker"
            bash "$OSINT_PUBLISH_SCRIPT" "$DOCKER_HUB_USERNAME"
            ;;
        3)
            print_info "Building all images (MCP first, then osint-tools)..."
            echo ""
            
            # Step 1: Build MCP images (fast)
            print_info "========================================="
            print_info "Step 1: Building MCP images..."
            print_info "========================================="
            if bash "$MCP_PUBLISH_SCRIPT"; then
                print_success "MCP images built successfully!"
            else
                print_error "MCP images build failed"
                exit 1
            fi
            
            echo ""
            print_info "========================================="
            print_info "Step 2: Building osint-tools..."
            print_info "========================================="
            print_warning "This will take 10-15 minutes..."
            read -p "Continue with osint-tools build? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cd "${SCRIPT_DIR}/docker"
                if bash "$OSINT_PUBLISH_SCRIPT" "$DOCKER_HUB_USERNAME"; then
                    print_success "osint-tools built successfully!"
                else
                    print_error "osint-tools build failed"
                    exit 1
                fi
            else
                print_info "Skipping osint-tools build"
            fi
            
            echo ""
            print_success "========================================="
            print_success "All images published successfully! 🎉"
            print_success "========================================="
            ;;
        4)
            print_info "Cancelled"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"

