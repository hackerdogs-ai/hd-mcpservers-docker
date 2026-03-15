#!/usr/bin/env python3
"""
Functional test for PDF Reader MCP Server (Docker-based).
Tests the @sylphx/pdf-reader-mcp server running in Docker container.
Uses direct JSON-RPC communication similar to OCR test.
"""

import json
import subprocess
import sys
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add project root to path
current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)
tools_dir = os.path.dirname(tests_dir)
modules_dir = os.path.dirname(tools_dir)
shared_dir = os.path.dirname(modules_dir)
project_root = os.path.dirname(shared_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from shared.modules.tools.mcp_docker_client import build_mcp_server_docker

logger = logging.getLogger(__name__)

# Configuration
PDF_URLS_FILE = Path(__file__).parent / "pdf_urls.txt"
RESULTS_FILE = Path(__file__).parent / "pdf_test_results.json"
REPORT_FILE = Path(__file__).parent / "PDF_FUNCTIONAL_TEST_REPORT.md"

# Docker image
IMAGE_NAME = "hackerdogs-mcp-pdf-reader-sylphx:latest"


def read_pdf_urls() -> List[str]:
    """Read PDF URLs from text file."""
    if not PDF_URLS_FILE.exists():
        logger.error(f"PDF URLs file not found: {PDF_URLS_FILE}")
        return []
    
    with open(PDF_URLS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    
    logger.info(f"Loaded {len(urls)} PDF URLs from {PDF_URLS_FILE}")
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
        
        # Read response
        response_line = process.stdout.readline()
        if not response_line:
            return None
        
        response = json.loads(response_line.strip())
        return response
    
    except Exception as e:
        logger.error(f"Error sending JSON-RPC request: {e}")
        return None


def test_pdf_reader_functional():
    """Functional test of PDF reader MCP server in Docker."""
    print("=" * 80)
    print("Functional Test: PDF Reader MCP Server in Docker")
    print("=" * 80)
    
    # Step 1: Build Docker image
    print("\n1. Building Docker image for PDF reader...")
    mcp_config = {
        "name": "pdf-reader-sylphx",
        "npm_package": "@sylphx/pdf-reader-mcp",
        "base_image": "node:20-slim",
        "entrypoint": "npx @sylphx/pdf-reader-mcp",
        "env": {
            "NODE_ENV": "production"
        }
    }
    
    docker_config = build_mcp_server_docker(mcp_config, force_rebuild=False)
    if not docker_config:
        print("❌ Failed to build Docker image")
        return False
    
    print(f"✅ Docker image ready: {IMAGE_NAME}")
    
    # Step 2: Read PDF URLs
    print("\n2. Reading PDF URLs...")
    pdf_urls = read_pdf_urls()
    
    if not pdf_urls:
        print(f"❌ No PDF URLs found in {PDF_URLS_FILE}")
        return False
    
    print(f"✅ Found {len(pdf_urls)} PDF URLs to test")
    
    # Step 3: Start MCP server in Docker
    print("\n3. Starting MCP server in Docker container...")
    
    docker_cmd = docker_config["command"]
    docker_args = docker_config["args"]
    
    # Build full command
    container_name = f"mcp-pdf-reader-test-{int(time.time())}"
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
        init_response = send_jsonrpc_request(
            server_process,
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "pdf-reader-test",
                    "version": "1.0.0"
                }
            },
            request_id=1
        )
        
        if init_response and "result" in init_response:
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
        tools_response = send_jsonrpc_request(
            server_process,
            "tools/list",
            {},
            request_id=2
        )
        
        if tools_response and "result" in tools_response:
            tools = tools_response["result"].get("tools", [])
            tool_names = [t.get("name", "unknown") for t in tools]
            print(f"✅ Available tools: {tool_names}")
        else:
            print(f"⚠️  Tools list response: {tools_response}")
    
    except Exception as e:
        print(f"⚠️  List tools error: {e}")
    
    # Step 6: Test PDF reading
    print("\n6. Testing PDF reading from URLs...")
    print("-" * 80)
    
    results = []
    request_id = 10
    
    for i, pdf_url in enumerate(pdf_urls, 1):
        print(f"\n   [{i}/{len(pdf_urls)}] Testing: {pdf_url[:60]}...")
        
        try:
            # Call read_pdf tool - check tool schema first to get correct parameters
            # Based on error, it might expect "sources" array instead of "url"
            pdf_request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": "read_pdf",
                    "arguments": {
                        "sources": [{"url": pdf_url}]
                    }
                }
            }
            
            request_str = json.dumps(pdf_request) + "\n"
            server_process.stdin.write(request_str)
            server_process.stdin.flush()
            
            # Read response (with timeout handling)
            time.sleep(3)  # Give PDF processing time
            
            response_line = None
            for _ in range(15):  # Try reading multiple times
                if server_process.stdout.readable():
                    line = server_process.stdout.readline()
                    if line:
                        response_line = line
                        break
                time.sleep(0.5)
            
            if not response_line:
                result = {
                    "url": pdf_url,
                    "status": "error",
                    "error": "No response from server"
                }
                print(f"      ❌ No response from server")
                results.append(result)
                request_id += 1
                continue
            
            pdf_response = json.loads(response_line.strip())
            
            if "error" in pdf_response:
                result = {
                    "url": pdf_url,
                    "status": "error",
                    "error": pdf_response["error"].get("message", "Unknown error")
                }
                print(f"      ❌ Error: {result['error']}")
            
            elif "result" in pdf_response:
                result_data = pdf_response["result"]
                
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
                    "url": pdf_url,
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
                    "url": pdf_url,
                    "status": "error",
                    "error": "Unexpected response format",
                    "response": pdf_response
                }
                print(f"      ❌ Unexpected response: {pdf_response}")
            
            results.append(result)
            request_id += 1
            time.sleep(1)  # Brief pause between requests
        
        except json.JSONDecodeError as e:
            result = {
                "url": pdf_url,
                "status": "error",
                "error": f"JSON decode error: {e}"
            }
            print(f"      ❌ JSON error: {e}")
            results.append(result)
            request_id += 1
        
        except Exception as e:
            result = {
                "url": pdf_url,
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
    
    print(f"\nTotal PDFs Tested: {len(results)}")
    print(f"Successful: {successful} ✅")
    print(f"Failed: {failed} ❌")
    if successful > 0:
        print(f"Total Text Extracted: {total_chars} characters, {total_words} words")
        print(f"Average per successful PDF: {total_chars // successful if successful else 0} chars, {total_words // successful if successful else 0} words")
    
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
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_pdfs": len(results),
            "successful": successful,
            "failed": failed,
            "total_text_chars": total_chars,
            "total_words": total_words,
            "results": results
        }, f, indent=2)
    
    print(f"\n✅ Results saved to: {RESULTS_FILE}")
    
    # Generate markdown report
    generate_report(successful, failed, total_chars, total_words, results)
    
    return successful > 0


def generate_report(successful: int, failed: int, total_chars: int, total_words: int, results: List[Dict]):
    """Generate markdown report from test results."""
    report_lines = [
        "# PDF Reader MCP Server - Functional Test Report",
        "",
        f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total PDFs Tested:** {len(results)}",
        f"**Successful:** {successful}",
        f"**Failed:** {failed}",
        f"**Success Rate:** {successful/len(results)*100:.1f}%" if results else "0%",
        f"**Total Text Extracted:** {total_chars} characters, {total_words} words",
        "",
        "## Test Results",
        ""
    ]
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result['status'] == 'success' else "❌ FAIL"
        report_lines.append(f"### {i}. {status} - {result['url']}")
        report_lines.append("")
        
        if result['status'] == 'success':
            report_lines.append(f"- **Text Length:** {result.get('text_length', 0)} characters")
            report_lines.append(f"- **Word Count:** {result.get('word_count', 0)} words")
            report_lines.append(f"- **Line Count:** {result.get('line_count', 0)} lines")
            if result.get('text_preview'):
                report_lines.append(f"- **Preview:** {result['text_preview'][:300]}...")
        else:
            report_lines.append(f"- **Error:** {result.get('error', 'Unknown error')}")
        
        report_lines.append("")
    
    with open(REPORT_FILE, "w") as f:
        f.write("\n".join(report_lines))
    
    logger.info(f"Report generated: {REPORT_FILE}")


def main():
    """Run functional test."""
    print("\n" + "=" * 80)
    print("PDF Reader MCP Docker Functional Test Suite")
    print("=" * 80)
    
    # Check Docker availability
    from shared.modules.tools.mcp_docker_client import get_mcp_docker_client
    client = get_mcp_docker_client()
    if not client or not client.docker_available:
        print("\n❌ Docker is not available. Please ensure Docker is running.")
        return 1
    
    print("\n✅ Docker is available")
    
    # Run functional test
    success = test_pdf_reader_functional()
    
    if success:
        print("\n🎉 Functional test completed successfully!")
        return 0
    else:
        print("\n⚠️  Functional test had issues. Check results above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
