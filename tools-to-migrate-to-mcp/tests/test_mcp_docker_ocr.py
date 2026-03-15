"""
Test script for MCP Docker Client with mcp-ocr

This script tests the dynamic Docker image building and execution
of the mcp-ocr MCP server.
"""

import os
import sys
import json

# Add project root to path
# Go up from: shared/modules/tools/tests/test_mcp_docker_ocr.py
# To: hackerdogs-core/
current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)
tools_dir = os.path.dirname(tests_dir)
modules_dir = os.path.dirname(tools_dir)
shared_dir = os.path.dirname(modules_dir)
project_root = os.path.dirname(shared_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.modules.tools.mcp_docker_client import build_mcp_server_docker, get_mcp_docker_client

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_mcp_ocr_build():
    """Test building mcp-ocr Docker image."""
    print("=" * 80)
    print("Testing MCP Docker Client with mcp-ocr")
    print("=" * 80)
    
    # MCP server configuration for mcp-ocr
    mcp_ocr_config = {
        "name": "ocr",
        "package_name": "mcp-ocr",
        "base_image": "python:3.11-slim",
        "additional_packages": [
            "tesseract-ocr",
            "tesseract-ocr-eng"  # English language pack
        ],
        "entrypoint": "python -m mcp_ocr",
        "env": {
            "PYTHONUNBUFFERED": "1"
        }
    }
    
    print("\n1. Building Docker image for mcp-ocr...")
    print(f"   Package: {mcp_ocr_config['package_name']}")
    print(f"   Base image: {mcp_ocr_config['base_image']}")
    print(f"   Additional packages: {mcp_ocr_config['additional_packages']}")
    
    # Build and configure
    result = build_mcp_server_docker(mcp_ocr_config, force_rebuild=False)
    
    if result:
        print("\n✅ Success! Docker image built and configured.")
        print("\n2. Generated MCP Configuration:")
        print(json.dumps({
            "mcpServers": {
                result["name"]: {
                    "command": result["command"],
                    "args": result["args"]
                }
            }
        }, indent=2))
        
        print("\n3. To use this in your MCP configuration:")
        print("   Add the above JSON to your MCP config file (e.g., ~/.cursor/mcp.json)")
        
        return True
    else:
        print("\n❌ Failed to build Docker image.")
        return False


def test_custom_dockerfile():
    """Test building with custom Dockerfile."""
    print("\n" + "=" * 80)
    print("Testing Custom Dockerfile Build")
    print("=" * 80)
    
    # Custom Dockerfile for mcp-ocr with more control
    custom_dockerfile = """FROM python:3.11-slim

# Install Tesseract OCR and language packs
RUN apt-get update && apt-get install -y \\
    tesseract-ocr \\
    tesseract-ocr-eng \\
    tesseract-ocr-fra \\
    && rm -rf /var/lib/apt/lists/*

# Install mcp-ocr
RUN pip install --no-cache-dir mcp-ocr

# Set entrypoint
ENTRYPOINT ["python", "-m", "mcp_ocr"]
"""
    
    mcp_config = {
        "name": "ocr-custom",
        "dockerfile": custom_dockerfile
    }
    
    print("\n1. Building with custom Dockerfile...")
    result = build_mcp_server_docker(mcp_config, force_rebuild=False)
    
    if result:
        print("\n✅ Success! Custom Dockerfile built.")
        print(f"   Image: hackerdogs-mcp-{result['name']}:latest")
        return True
    else:
        print("\n❌ Failed to build with custom Dockerfile.")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("MCP Docker Client Test Suite")
    print("=" * 80)
    
    # Check Docker availability
    client = get_mcp_docker_client()
    if not client or not client.docker_available:
        print("\n❌ Docker is not available. Please ensure Docker is running.")
        return 1
    
    print("\n✅ Docker is available")
    
    # Test 1: Build mcp-ocr from pip package
    success1 = test_mcp_ocr_build()
    
    # Test 2: Build with custom Dockerfile
    success2 = test_custom_dockerfile()
    
    # Summary
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"Pip package build: {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Custom Dockerfile build: {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

