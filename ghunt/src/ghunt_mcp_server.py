#!/usr/bin/env python3
"""
GHunt MCP Server
A dedicated MCP server for GHunt Google account search.
"""

import asyncio
import json
import os
import sys
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

async def handle_ghunt(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GHunt Google account search."""
    identifier = params["identifier"]
    timeout = params.get("timeout", 10000)
    
    cwd = "/opt/ghunt"
    extra_env = {"PYTHONPATH": "/opt/ghunt"}
    
    if os.path.exists("/opt/ghunt/main.py"):
        cmd = ["python3", "/opt/ghunt/main.py", "email", identifier]
    elif os.path.exists("/opt/ghunt/ghunt.py"):
        cmd = ["python3", "/opt/ghunt/ghunt.py", "email", identifier]
    else:
        cmd = ["python3", "-c", 
               "import sys; sys.path.insert(0, '/opt/ghunt'); from ghunt import ghunt; ghunt.main()",
               "email", identifier]
    
    stdout, stderr, returncode = await run_command_in_venv(
        cmd, 
        cwd=cwd if os.path.exists(cwd) else None,
        extra_env=extra_env
    )
    
    if returncode == 0:
        return {"success": True, "content": stdout}
    else:
        return {"success": False, "error": f"GHunt failed: {stderr}"}

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
                                "name": "ghunt-mcp-server",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    tools = [
                        {
                            "name": "ghunt_google_search",
                            "description": "Search for Google account information using email address or Google ID. API keys can be provided via environment variables (GOOGLE_API_KEY, GOOGLE_CX) for enhanced searches.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "identifier": {"type": "string", "description": "Email address or Google ID to search"},
                                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 10000)"}
                                },
                                "required": ["identifier"]
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
                    
                    if tool_name == "ghunt_google_search":
                        result = await handle_ghunt(tool_params)
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

