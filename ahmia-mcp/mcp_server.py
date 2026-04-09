#!/usr/bin/env python3
"""Ahmia MCP Server — search Tor hidden services via Ahmia.fi."""
import json, logging, os, re, sys
import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("ahmia-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8510"))
mcp = FastMCP("Ahmia MCP Server", instructions="Search Tor hidden services via Ahmia.fi.")

@mcp.tool()
def ahmia_search(query: str, max_results: int = 50) -> str:
    """Search Ahmia.fi for Tor hidden service results.
    Args:
        query: Search query.
        max_results: Max results to return.
    """
    try:
        r = httpx.get(f"https://ahmia.fi/search/?q={query}", timeout=30, follow_redirects=True, headers={"User-Agent": "ahmia-mcp/1.0"})
        r.raise_for_status()
        onions = list(set(re.findall(r'https?://[a-z2-7]{56}\.onion[^\s"<>]*', r.text)))[:max_results]
        return json.dumps({"query": query, "results": onions, "count": len(onions)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting ahmia-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
