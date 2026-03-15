#!/usr/bin/env python3
"""
theHarvester MCP Server
A dedicated MCP server for theHarvester domain/email enumeration.
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

async def handle_theharvester(params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle theHarvester domain/email enumeration."""
    domain = params["domain"]
    sources = params.get("sources", "all")
    limit = params.get("limit", 500)
    
    api_keys = {}
    if "hunter_api_key" in params:
        api_keys["HUNTER_API_KEY"] = params["hunter_api_key"]
    if "bing_api_key" in params:
        api_keys["BING_API_KEY"] = params["bing_api_key"]
    if "shodan_api_key" in params:
        api_keys["SHODAN_API_KEY"] = params["shodan_api_key"]
    if "securitytrails_api_key" in params:
        api_keys["SECURITYTRAILS_API_KEY"] = params["securitytrails_api_key"]
    
    script_path = "/opt/theharvester/theHarvester.py"
    if os.path.exists(script_path):
        cmd = ["python3", script_path, "-d", domain, "-b", sources, "-l", str(limit)]
        stdout, stderr, returncode = await run_command_in_venv(cmd, extra_env=api_keys, cwd="/opt/theharvester")
        
        if returncode == 0:
            return {"success": True, "content": stdout}
        else:
            return {"success": False, "error": f"theHarvester failed: {stderr}"}
    else:
        return {"success": False, "error": "theHarvester script not found at /opt/theharvester/theHarvester.py"}

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
                                "name": "theharvester-mcp-server",
                                "version": "1.0.0"
                            }
                        }
                    }
                elif method == "tools/list":
                    tools = [
                        {
                            "name": "theharvester_domain_search",
                            "description": "Gather emails, subdomains, hosts, employee names, open ports and banners from public sources. API keys can be provided via environment variables or optional parameters for enhanced sources (hunter, bingapi, shodan, securityTrails).",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "domain": {"type": "string", "description": "Domain/company name to search"},
                                    "sources": {"type": "string", "description": "Data sources (default: all). Options: baidu, bing, bingapi, certspotter, crtsh, dnsdumpster, duckduckgo, github-code, google, hackertarget, hunter, linkedin, linkedin_links, otx, pentesttools, projectdiscovery, qwant, rapiddns, securityTrails, sublist3r, threatcrowd, threatminer, trello, twitter, urlscan, virustotal, yahoo"},
                                    "limit": {"type": "integer", "description": "Limit results (default: 500)"},
                                    "hunter_api_key": {"type": "string", "description": "Optional: Hunter.io API key for enhanced email discovery"},
                                    "bing_api_key": {"type": "string", "description": "Optional: Bing API key for bingapi source"},
                                    "shodan_api_key": {"type": "string", "description": "Optional: Shodan API key for shodan source"},
                                    "securitytrails_api_key": {"type": "string", "description": "Optional: SecurityTrails API key for securityTrails source"}
                                },
                                "required": ["domain"]
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
                    
                    if tool_name == "theharvester_domain_search":
                        result = await handle_theharvester(tool_params)
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

