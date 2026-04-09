#!/usr/bin/env python3
"""Apple iTunes MCP Server — search iTunes for apps by domain."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("apple-itunes-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8511"))
mcp = FastMCP("Apple iTunes MCP Server", instructions="Search Apple iTunes for apps associated with a domain.")

@mcp.tool()
def itunes_search_apps(domain: str, limit: int = 25) -> str:
    """Search iTunes for apps whose bundle ID matches a domain.
    Args:
        domain: Domain to search for (e.g. example.com).
        limit: Max results (default 25).
    """
    try:
        r = httpx.get("https://itunes.apple.com/search", params={"term": domain, "entity": "software", "limit": limit}, timeout=30)
        r.raise_for_status()
        data = r.json()
        apps = [{"name": a.get("trackName"), "bundleId": a.get("bundleId"), "seller": a.get("sellerName"), "url": a.get("trackViewUrl")} for a in data.get("results", [])]
        return json.dumps({"domain": domain, "apps": apps, "count": len(apps)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting apple-itunes-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
