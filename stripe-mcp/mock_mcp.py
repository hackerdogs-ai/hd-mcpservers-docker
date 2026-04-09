#!/usr/bin/env python3
"""Lightweight mock MCP server for remote-proxy servers that need valid credentials.

Returns a valid initialize response and a placeholder tool list so the container
passes protocol-level health checks without real API keys.

Usage: mock_mcp.py <server_name> <description> [port]
"""
import json, sys


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "mock-mcp"
    desc = sys.argv[2] if len(sys.argv) > 2 else "Mock MCP server"

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method", "")
        msg_id = msg.get("id")

        if method == "initialize":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": name, "version": "1.0.0"},
                    "instructions": desc,
                },
            }
            print(json.dumps(resp), flush=True)

        elif method == "notifications/initialized":
            pass

        elif method == "tools/list":
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": [
                        {
                            "name": f"{name.replace('-mcp','')}_health_check",
                            "description": f"Health check for {name} (placeholder — supply real API keys for full tool list)",
                            "inputSchema": {"type": "object", "properties": {}},
                        }
                    ]
                },
            }
            print(json.dumps(resp), flush=True)

        elif msg_id is not None:
            resp = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Mock server: real API credentials required for {method}",
                },
            }
            print(json.dumps(resp), flush=True)


if __name__ == "__main__":
    main()
