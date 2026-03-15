#!/usr/bin/env python3
"""
Test suite for Maigret MCP Server.
Tests the Maigret username search tool.
"""

import json
import subprocess
import sys
import time
from typing import Dict, Any

def send_mcp_request(docker_cmd, method, params=None, request_id=1):
    """Send a JSON-RPC request to the MCP server running in Docker."""
    request = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method
    }
    if params:
        request["params"] = params
    
    request_json = json.dumps(request) + "\n"
    
    process = subprocess.Popen(
        docker_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        stdout, stderr = process.communicate(input=request_json, timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        return {"error": "Request timeout", "timeout": True}
    
    if stderr:
        print(f"Stderr: {stderr}", file=sys.stderr)
    
    try:
        response_line = stdout.strip().split('\n')[0] if stdout.strip() else ""
        if response_line:
            return json.loads(response_line)
        else:
            return {"error": "No response received", "stdout": stdout, "stderr": stderr}
    except json.JSONDecodeError as e:
        return {"error": f"JSON decode error: {e}", "stdout": stdout, "stderr": stderr}

def test_tool(docker_cmd, tool_name, arguments, test_name, timeout=30):
    """Test a specific tool."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")
    print(f"Tool: {tool_name}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    
    start_time = time.time()
    response = send_mcp_request(
        docker_cmd,
        "tools/call",
        {
            "name": tool_name,
            "arguments": arguments
        },
        request_id=3
    )
    elapsed = time.time() - start_time
    
    if "error" in response:
        if response.get("timeout"):
            print(f"⏱️  Tool timed out after {timeout}s")
            return False
        else:
            print(f"❌ Tool call failed: {response.get('error')}")
            return False
    
    if "result" in response:
        print(f"✅ Tool executed successfully ({elapsed:.2f}s)")
        if "content" in response["result"]:
            try:
                result_data = json.loads(response["result"]["content"][0].get("text", "{}"))
                if result_data.get("success"):
                    content = result_data.get("content", "")
                    if isinstance(content, str):
                        print(f"   Result length: {len(content)} characters")
                    elif isinstance(content, dict):
                        print(f"   Result keys: {list(content.keys())}")
                else:
                    print(f"   Tool returned error: {result_data.get('error', 'Unknown')}")
            except:
                print(f"   Response received (parsing skipped)")
        return True
    else:
        print(f"❌ Unexpected response format")
        return False

def main():
    """Run tests for Maigret."""
    print("="*60)
    print("Maigret MCP Server Test Suite")
    print("="*60)
    
    docker_cmd = ["docker", "run", "--rm", "-i", "hackerdogs/maigret-mcp-server:latest"]
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: Initialize
    tests_total += 1
    response = send_mcp_request(docker_cmd, "initialize", request_id=1)
    if "result" in response and response["result"].get("serverInfo", {}).get("name") == "maigret-mcp-server":
        print("✅ Initialize successful")
        tests_passed += 1
    else:
        print("❌ Initialize failed")
    
    # Test 2: List tools
    tests_total += 1
    response = send_mcp_request(docker_cmd, "tools/list", request_id=2)
    if "result" in response and "tools" in response["result"]:
        tools = response["result"]["tools"]
        if len(tools) > 0 and tools[0].get("name") == "maigret_username_search":
            print("✅ Tools list successful")
            tests_passed += 1
        else:
            print("❌ Tools list failed - wrong tool name")
    else:
        print("❌ Tools list failed")
    
    # Test 3: Maigret username search
    tests_total += 1
    if test_tool(
        docker_cmd,
        "maigret_username_search",
        {"username": "testuser", "timeout": 5},
        "Maigret Username Search (Quick Test)"
    ):
        tests_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"Tests failed: {tests_total - tests_passed}")
    
    if tests_passed == tests_total:
        print("✅ All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

