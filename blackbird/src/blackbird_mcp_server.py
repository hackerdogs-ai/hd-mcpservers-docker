#!/usr/bin/env python3
"""
Blackbird MCP Server
A dedicated MCP server for Blackbird username search tool.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

async def run_command_in_venv(command: list[str], cwd: Optional[str] = None, input_data: Optional[str] = None, extra_env: Optional[Dict[str, str]] = None) -> tuple[str, str, int]:
    """Run a command in the virtual environment."""
    try:
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)
        
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            stdin=asyncio.subprocess.PIPE if input_data else None
        )
        
        stdout, stderr = await process.communicate(input=input_data.encode() if input_data else None)
        
        return stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore'), process.returncode
        
    except Exception as e:
        return "", str(e), 1

async def handle_blackbird(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Blackbird username search."""
    username = params["username"]
    timeout = params.get("timeout", 10000)
    
    data_dir = "/app/data"
    os.makedirs(data_dir, exist_ok=True)
    
    extra_env = {
        "BLACKBIRD_DATA_DIR": data_dir,
        "USERNAME_LIST_PATH": os.path.join(data_dir, "wmn-data.json")
    }
    
    data_file = extra_env["USERNAME_LIST_PATH"]
    if not os.path.exists(data_file):
        Path(data_file).parent.mkdir(parents=True, exist_ok=True)
        Path(data_file).write_text("{}")
    
    cmd = ["python3", "/opt/blackbird/blackbird.py", "-u", username, "--timeout", str(timeout)]
    
    stdout, stderr, returncode = await run_command_in_venv(cmd, extra_env=extra_env, cwd="/opt/blackbird")
    
    if returncode == 0:
        return {"success": True, "content": stdout}
    else:
        return {"success": False, "error": f"Blackbird failed: {stderr}"}

async def main():
    """Main MCP server loop - handles JSON-RPC over stdio."""
    try:
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line.strip())
                method = request.get("method")
                params = request.get("params", {})
                request_id = request.get("id")
                
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "blackbird-mcp-server",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    tools = [
                        {
                            "name": "blackbird_username_search",
                            "description": "Fast OSINT tool to search for accounts by username across 581 sites",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "username": {"type": "string", "description": "Username to search for"},
                                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 10000)"}
                                },
                                "required": ["username"]
                            }
                        }
                    ]
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {"tools": tools}
                    }
                elif method == "tools/call":
                    tool_name = params.get("name")
                    tool_params = params.get("arguments", {})
                    
                    if tool_name == "blackbird_username_search":
                        result = await handle_blackbird(tool_params)
                    else:
                        result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                    
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, indent=2)
                                }
                            ]
                        }
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                
                print(json.dumps(response), flush=True)
                
            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response), flush=True)
                
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())

