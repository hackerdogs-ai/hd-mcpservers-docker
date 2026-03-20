#!/usr/bin/env python3
"""Archive.org MCP Server — Wayback Machine snapshot lookups."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("archiveorg-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8512"))
mcp = FastMCP("Archive.org MCP Server", instructions="Query Wayback Machine for archived snapshots of URLs.")

@mcp.tool()
def wayback_lookup(url: str) -> str:
    """Check if a URL has Wayback Machine snapshots.
    Args:
        url: URL to look up.
    """
    try:
        r = httpx.get(f"https://archive.org/wayback/available?url={url}", timeout=30)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting archiveorg-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
