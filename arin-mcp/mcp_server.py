#!/usr/bin/env python3
"""ARIN MCP Server — ARIN Whois REST API lookups."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("arin-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8513"))
mcp = FastMCP("ARIN MCP Server", instructions="Query ARIN Whois REST API for IP and organization information.")

@mcp.tool()
def arin_lookup(query: str) -> str:
    """Look up an IP address or organization in ARIN Whois.
    Args:
        query: IP address, CIDR, or org handle to look up.
    """
    try:
        r = httpx.get(f"https://whois.arin.net/rest/ip/{query}", headers={"Accept": "application/json"}, timeout=30, follow_redirects=True)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError:
        try:
            r2 = httpx.get(f"https://whois.arin.net/rest/org/{query}", headers={"Accept": "application/json"}, timeout=30, follow_redirects=True)
            r2.raise_for_status()
            return json.dumps(r2.json(), indent=2)
        except Exception as e2:
            return json.dumps({"error": str(e2)})
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting arin-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
