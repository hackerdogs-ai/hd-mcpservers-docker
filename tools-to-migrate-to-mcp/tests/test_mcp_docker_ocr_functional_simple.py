"""
Functional Test for MCP Docker OCR Server (Simple Version)

This script tests the mcp-ocr server running in Docker by:
1. Building the Docker image (if needed)
2. Starting the MCP server in a Docker container
3. Sending JSON-RPC requests directly via stdio
4. Testing OCR on multiple images from URLs
5. Reporting results

This version doesn't require the MCP SDK - it communicates directly via JSON-RPC.
"""

import os
import sys
import json
import time
import subprocess
from typing import List, Dict, Any, Optional

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


def send_jsonrpc_request(process, method: str, params: Dict[str, Any], request_id: int = 1) -> Optional[Dict[str, Any]]:
    """Send JSON-RPC request to MCP server and get response."""
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": params
    }
    
    request_str = json.dumps(request) + "\n"
    
    try:
        # Send request
        process.stdin.write(request_str)
        process.stdin.flush()
        
        # Read response (with timeout)
        import select
        import sys
        
        # Wait for response (simple approach - read line)
        response_line = process.stdout.readline()
        if not response_line:
            return None
        
        response = json.loads(response_line.strip())
        return response
    
    except Exception as e:
        logger.error(f"Error sending JSON-RPC request: {e}")
        return None


def test_mcp_ocr_functional():
    """Functional test of mcp-ocr server in Docker."""
    print("=" * 80)
    print("Functional Test: MCP OCR Server in Docker (Simple JSON-RPC)")
    print("=" * 80)
    
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
    
    docker_cmd = docker_config["command"]
    docker_args = docker_config["args"]
    
    # Build full command
    container_name = f"mcp-ocr-test-{int(time.time())}"
    args = ["run", "--rm", "-i", "--name", container_name]
    
    # Add environment variables
    for i, arg in enumerate(docker_args):
        if arg == "--env" and i + 1 < len(docker_args):
            args.extend(["--env", docker_args[i + 1]])
    
    # Add image name (last arg)
    args.append(docker_args[-1])
    
    print(f"   Command: {docker_cmd} {' '.join(args[:10])}...")
    
    # Start the server process
    try:
        server_process = subprocess.Popen(
            [docker_cmd] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Give it a moment to start
        time.sleep(3)
        
        if server_process.poll() is not None:
            stderr = server_process.stderr.read() if server_process.stderr else ""
            print(f"❌ Server process exited immediately. stderr: {stderr[:500]}")
            return False
        
        print("✅ MCP server started in Docker")
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 4: Initialize MCP session
    print("\n4. Initializing MCP session...")
    
    try:
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        request_str = json.dumps(init_request) + "\n"
        server_process.stdin.write(request_str)
        server_process.stdin.flush()
        
        # Read initialize response
        time.sleep(1)
        response_line = server_process.stdout.readline()
        if response_line:
            init_response = json.loads(response_line.strip())
            if "result" in init_response:
                print(f"✅ Session initialized: {init_response.get('result', {}).get('protocolVersion', 'unknown')}")
            else:
                print(f"⚠️  Initialize response: {init_response}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        server_process.stdin.write(json.dumps(initialized_notification) + "\n")
        server_process.stdin.flush()
        time.sleep(0.5)
        
    except Exception as e:
        print(f"⚠️  Initialize error (continuing anyway): {e}")
    
    # Step 5: List tools
    print("\n5. Listing available tools...")
    
    try:
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        server_process.stdin.write(json.dumps(list_tools_request) + "\n")
        server_process.stdin.flush()
        
        time.sleep(1)
        response_line = server_process.stdout.readline()
        if response_line:
            tools_response = json.loads(response_line.strip())
            if "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                tool_names = [t.get("name", "unknown") for t in tools]
                print(f"✅ Available tools: {tool_names}")
            else:
                print(f"⚠️  Tools list response: {tools_response}")
    
    except Exception as e:
        print(f"⚠️  List tools error: {e}")
    
    # Step 6: Test OCR on images
    print("\n6. Testing OCR on images...")
    print("-" * 80)
    
    results = []
    request_id = 10
    
    for i, image_url in enumerate(image_urls, 1):
        print(f"\n   [{i}/{len(image_urls)}] Testing: {image_url[:60]}...")
        
        try:
            # Call perform_ocr tool (parameter is "input_data" not "image")
            ocr_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "perform_ocr",
                    "arguments": {
                        "input_data": image_url
                    }
                }
            }
            
            request_str = json.dumps(ocr_request) + "\n"
            server_process.stdin.write(request_str)
            server_process.stdin.flush()
            
            # Read response (with timeout handling)
            time.sleep(2)  # Give OCR time to process
            
            response_line = None
            for _ in range(10):  # Try reading multiple times
                if server_process.stdout.readable():
                    line = server_process.stdout.readline()
                    if line:
                        response_line = line
                        break
                time.sleep(0.5)
            
            if not response_line:
                result = {
                    "url": image_url,
                    "status": "error",
                    "error": "No response from server"
                }
                print(f"      ❌ No response from server")
                results.append(result)
                request_id += 1
                continue
            
            ocr_response = json.loads(response_line.strip())
            
            if "error" in ocr_response:
                result = {
                    "url": image_url,
                    "status": "error",
                    "error": ocr_response["error"].get("message", "Unknown error")
                }
                print(f"      ❌ Error: {result['error']}")
            
            elif "result" in ocr_response:
                result_data = ocr_response["result"]
                
                # Extract text from content
                text_content = ""
                if "content" in result_data:
                    for content_item in result_data["content"]:
                        if isinstance(content_item, dict):
                            if "text" in content_item:
                                text_content += content_item["text"]
                            elif "type" in content_item and content_item["type"] == "text":
                                text_content += content_item.get("text", "")
                
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
                    "status": "error",
                    "error": "Unexpected response format",
                    "response": ocr_response
                }
                print(f"      ❌ Unexpected response: {ocr_response}")
            
            results.append(result)
            request_id += 1
            time.sleep(1)  # Brief pause between requests
        
        except json.JSONDecodeError as e:
            result = {
                "url": image_url,
                "status": "error",
                "error": f"JSON decode error: {e}"
            }
            print(f"      ❌ JSON error: {e}")
            results.append(result)
            request_id += 1
        
        except Exception as e:
            result = {
                "url": image_url,
                "status": "error",
                "error": str(e)
            }
            print(f"      ❌ Exception: {e}")
            results.append(result)
            request_id += 1
    
    # Cleanup
    try:
        server_process.terminate()
        time.sleep(1)
        if server_process.poll() is None:
            server_process.kill()
    except:
        pass
    
    # Step 7: Report results
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
    if successful > 0:
        print(f"Total Text Extracted: {total_chars} characters, {total_words} words")
        print(f"Average per successful image: {total_chars // successful if successful else 0} chars, {total_words // successful if successful else 0} words")
    
    print("\n" + "-" * 80)
    print("Detailed Results:")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result['url'][:70]}...")
        print(f"   Status: {result['status']}")
        if result['status'] == 'success':
            print(f"   Text: {result.get('text_length', 0)} chars, {result.get('word_count', 0)} words, {result.get('line_count', 0)} lines")
            if result.get('text_preview'):
                preview = result['text_preview'][:150].replace('\n', ' ')
                print(f"   Preview: {preview}")
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
    print("MCP Docker OCR Functional Test Suite (Simple JSON-RPC)")
    print("=" * 80)
    
    # Check Docker availability
    client = get_mcp_docker_client()
    if not client or not client.docker_available:
        print("\n❌ Docker is not available. Please ensure Docker is running.")
        return 1
    
    print("\n✅ Docker is available")
    
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

