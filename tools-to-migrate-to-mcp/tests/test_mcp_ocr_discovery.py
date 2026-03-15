"""
Diagnostic test for OCR MCP server tool discovery issue.

This script tests the exact configuration format that the MCP client uses
to diagnose why tools aren't being discovered.
"""

import asyncio
import json
import sys
import os

# Add project root to path
current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)
tools_dir = os.path.dirname(tests_dir)
modules_dir = os.path.dirname(tools_dir)
shared_dir = os.path.dirname(modules_dir)
project_root = os.path.dirname(shared_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)

from streamlit_app.modules.mcp_registry import MCPRegistry


async def test_discovery():
    """Test tool discovery with the exact config from database."""
    
    # Simulate the server config as it would come from the database
    server_config = {
        'instance_name': 'ocr_mcp_server_2',
        'tool_instance_id': 'test-ocr-001',
        'server_type': 'stdio',
        'mcp_config': {
            'server_type': 'stdio',
            'stdio': {
                'command': 'docker',
                'args': [
                    'run',
                    '--rm',
                    '-i',
                    '--env',
                    'PYTHONUNBUFFERED=1',
                    'hackerdogs-mcp-ocr:latest'
                ],
                'env': {}
            }
        },
        'environment_variables': {}
    }
    
    print("=" * 60)
    print("Testing OCR MCP Server Tool Discovery")
    print("=" * 60)
    print(f"\nServer Config:")
    print(json.dumps(server_config, indent=2, default=str))
    
    registry = MCPRegistry()
    
    try:
        print("\n1. Building FastMCP Client config...")
        client_config = registry._build_fastmcp_client_config(server_config)
        
        if not client_config:
            print("❌ Failed to build client config")
            return
        
        print(f"✅ Client config built:")
        print(json.dumps(client_config, indent=2, default=str))
        
        print("\n2. Discovering tools...")
        tools = await registry.discover_tools('ocr_mcp_server_2', server_config)
        
        print(f"\n✅ Discovery complete: {len(tools)} tools found")
        for tool in tools:
            print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')[:80]}")
        
        if not tools:
            print("\n❌ No tools discovered!")
            print("\n3. Testing connection...")
            success, message = await registry.test_connection(server_config)
            print(f"Connection test: {success} - {message}")
        
    except Exception as e:
        print(f"\n❌ Error during discovery: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_discovery())


