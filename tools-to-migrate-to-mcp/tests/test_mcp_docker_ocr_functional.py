"""
Functional Test for MCP Docker OCR Server

This script tests the mcp-ocr server running in Docker by:
1. Building the Docker image (if needed)
2. Starting the MCP server in a Docker container
3. Connecting to it via MCP protocol
4. Testing OCR on multiple images from URLs
5. Reporting results
"""

import os
import sys
import json
import time
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)
tools_dir = os.path.dirname(tests_dir)
modules_dir = os.path.dirname(tools_dir)
shared_dir = os.path.dirname(modules_dir)
project_root = os.path.dirname(shared_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger.warning("MCP SDK not available. Install with: pip install mcp")

from shared.modules.tools.mcp_docker_client import build_mcp_server_docker, get_mcp_docker_client


def read_image_urls(file_path: str) -> List[str]:
    """Read image URLs from file."""
    urls = []
    if not os.path.exists(file_path):
        logger.error(f"Image URLs file not found: {file_path}")
        return urls
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                urls.append(line)
    
    return urls


def test_mcp_ocr_functional():
    """Functional test of mcp-ocr server in Docker."""
    print("=" * 80)
    print("Functional Test: MCP OCR Server in Docker")
    print("=" * 80)
    
    if not MCP_AVAILABLE:
        print("\n❌ MCP SDK not available. Install with: pip install mcp")
        return False
    
    # Step 1: Build Docker image
    print("\n1. Building Docker image for mcp-ocr...")
    mcp_config = {
        "name": "ocr",
        "package_name": "mcp-ocr",
        "base_image": "python:3.11-slim",
        "additional_packages": ["tesseract-ocr", "tesseract-ocr-eng"],
        "entrypoint": "python -m mcp_ocr"
    }
    
    docker_config = build_mcp_server_docker(mcp_config, force_rebuild=False)
    if not docker_config:
        print("❌ Failed to build Docker image")
        return False
    
    print(f"✅ Docker image ready: hackerdogs-mcp-ocr:latest")
    
    # Step 2: Read image URLs
    print("\n2. Reading image URLs...")
    test_dir = os.path.dirname(os.path.abspath(__file__))
    urls_file = os.path.join(test_dir, "images_urls.txt")
    image_urls = read_image_urls(urls_file)
    
    if not image_urls:
        print(f"❌ No image URLs found in {urls_file}")
        return False
    
    print(f"✅ Found {len(image_urls)} image URLs to test")
    
    # Step 3: Start MCP server in Docker
    print("\n3. Starting MCP server in Docker container...")
    
    # Build command to start server
    docker_cmd = docker_config["command"]
    docker_args = docker_config["args"]
    
    # Remove --name from args (we'll use a unique name)
    # Also ensure we're using interactive mode
    container_name = f"mcp-ocr-test-{int(time.time())}"
    args = ["run", "--rm", "-i", "--name", container_name]
    
    # Add environment variables
    for i, arg in enumerate(docker_args):
        if arg == "--env" and i + 1 < len(docker_args):
            args.extend(["--env", docker_args[i + 1]])
    
    # Add image name (last arg)
    args.append(docker_args[-1])
    
    print(f"   Command: {docker_cmd} {' '.join(args)}")
    
    # Start the server process
    try:
        server_process = subprocess.Popen(
            [docker_cmd] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        if server_process.poll() is not None:
            stderr = server_process.stderr.read() if server_process.stderr else ""
            print(f"❌ Server process exited immediately. stderr: {stderr}")
            return False
        
        print("✅ MCP server started in Docker")
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False
    
    # Step 4: Connect to MCP server and test OCR
    print("\n4. Testing OCR on images...")
    print("-" * 80)
    
    results = []
    
    try:
        # Create MCP client session
        server_params = StdioServerParameters(
            command=docker_cmd,
            args=args,
            env=None
        )
        
        with stdio_client(server_params) as (read, write):
            with ClientSession(read, write) as session:
                # Initialize the session
                init_result = session.initialize()
                print(f"   Session initialized: {init_result.protocol_version}")
                
                # List available tools
                tools_result = session.list_tools()
                print(f"   Available tools: {[tool.name for tool in tools_result.tools]}")
                
                # Test each image URL
                for i, image_url in enumerate(image_urls, 1):
                    print(f"\n   [{i}/{len(image_urls)}] Testing: {image_url[:60]}...")
                    
                    try:
                        # Call perform_ocr tool
                        ocr_result = session.call_tool(
                            "perform_ocr",
                            arguments={"image": image_url}
                        )
                        
                        # Extract text from result
                        if ocr_result.content:
                            text_content = ""
                            for content in ocr_result.content:
                                if hasattr(content, 'text'):
                                    text_content += content.text
                                elif isinstance(content, dict) and 'text' in content:
                                    text_content += content['text']
                            
                            # Count words/lines
                            words = len(text_content.split()) if text_content else 0
                            lines = len(text_content.split('\n')) if text_content else 0
                            
                            result = {
                                "url": image_url,
                                "status": "success",
                                "text_length": len(text_content),
                                "word_count": words,
                                "line_count": lines,
                                "text_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
                            }
                            
                            print(f"      ✅ Success: {words} words, {lines} lines extracted")
                            if text_content:
                                preview = text_content[:100].replace('\n', ' ')
                                print(f"      Preview: {preview}...")
                            else:
                                print(f"      ⚠️  No text extracted")
                        
                        else:
                            result = {
                                "url": image_url,
                                "status": "success",
                                "text_length": 0,
                                "word_count": 0,
                                "line_count": 0,
                                "text_preview": "",
                                "note": "No content returned"
                            }
                            print(f"      ⚠️  No content returned")
                        
                    except Exception as e:
                        result = {
                            "url": image_url,
                            "status": "error",
                            "error": str(e)
                        }
                        print(f"      ❌ Error: {e}")
                    
                    results.append(result)
                    time.sleep(1)  # Brief pause between requests
        
    except Exception as e:
        print(f"\n❌ MCP client error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup: stop the server process
        try:
            server_process.terminate()
            server_process.wait(timeout=5)
        except:
            server_process.kill()
    
    # Step 5: Report results
    print("\n" + "=" * 80)
    print("Test Results Summary")
    print("=" * 80)
    
    successful = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - successful
    total_words = sum(r.get("word_count", 0) for r in results)
    total_chars = sum(r.get("text_length", 0) for r in results)
    
    print(f"\nTotal Images Tested: {len(results)}")
    print(f"Successful: {successful} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Total Text Extracted: {total_chars} characters, {total_words} words")
    print(f"\nAverage per image: {total_chars // len(results) if results else 0} chars, {total_words // len(results) if results else 0} words")
    
    print("\n" + "-" * 80)
    print("Detailed Results:")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['url'][:70]}...")
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   Text: {result.get('text_length', 0)} chars, {result.get('word_count', 0)} words, {result.get('line_count', 0)} lines")
            if result.get('text_preview'):
                print(f"   Preview: {result['text_preview'][:150]}")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")
    
    # Save results to JSON file
    results_file = os.path.join(os.path.dirname(__file__), "ocr_test_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_images": len(results),
            "successful": successful,
            "failed": failed,
            "total_text_chars": total_chars,
            "total_words": total_words,
            "results": results
        }, f, indent=2)
    
    print(f"\n✅ Results saved to: {results_file}")
    
    return successful > 0


def main():
    """Run functional test."""
    print("\n" + "=" * 80)
    print("MCP Docker OCR Functional Test Suite")
    print("=" * 80)
    
    # Check Docker availability
    client = get_mcp_docker_client()
    if not client or not client.docker_available:
        print("\n❌ Docker is not available. Please ensure Docker is running.")
        return 1
    
    print("\n✅ Docker is available")
    
    if not MCP_AVAILABLE:
        print("\n❌ MCP SDK is not available. Install with: pip install mcp")
        return 1
    
    print("✅ MCP SDK is available")
    
    # Run functional test
    success = test_mcp_ocr_functional()
    
    if success:
        print("\n🎉 Functional test completed successfully!")
        return 0
    else:
        print("\n⚠️  Functional test had issues. Check results above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())


