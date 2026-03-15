#!/usr/bin/env python3
"""
Sherlock MCP Server
A dedicated MCP server for Sherlock username search tool.
"""

import asyncio
import json
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

async def run_command_in_venv(command: List[str], cwd: Optional[str] = None, input_data: Optional[str] = None, extra_env: Optional[Dict[str, str]] = None) -> tuple[str, str, int]:
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

async def handle_sherlock(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle Sherlock username search."""
    username = params["username"]
    timeout = params.get("timeout", 10000)
    sites = params.get("sites", [])
    output_format = params.get("output_format", "csv")
    
    cmd = ["sherlock", username, f"--timeout", str(timeout)]
    
    if sites:
        for site in sites:
            cmd.extend(["--site", site])
            
    if output_format == "csv":
        cmd.append("--csv")
    elif output_format == "xlsx":
        cmd.append("--xlsx")
        
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        cmd.extend(["--folderoutput", temp_dir])
        
        stdout, stderr, returncode = await run_command_in_venv(cmd)
        
        if returncode == 0:
            # Read output files
            output_files = list(Path(temp_dir).glob(f"{username}.*"))
            results = {"stdout": stdout, "files": []}
            
            for file_path in output_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    results["files"].append({
                        "filename": file_path.name,
                        "content": content
                    })
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}", file=sys.stderr)
            
            return {"success": True, "content": results}
        else:
            return {"success": False, "error": f"Sherlock failed: {stderr}"}

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
                                "name": "sherlock-mcp-server",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    tools = [
                        {
                            "name": "sherlock_username_search",
                            "description": "Search for username across 399+ social media platforms and websites",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "username": {"type": "string", "description": "Username to search for"},
                                    "timeout": {"type": "integer", "description": "Timeout in seconds (default: 10000)"},
                                    "sites": {"type": "array", "items": {"type": "string"}, "description": "Specific sites to search"},
                                    "output_format": {"type": "string", "enum": ["txt", "csv", "xlsx"], "description": "Output format"}
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
                    
                    if tool_name == "sherlock_username_search":
                        result = await handle_sherlock(tool_params)
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

