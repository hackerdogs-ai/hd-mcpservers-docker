#!/usr/bin/env python3
"""Bitbucket MCP Server — code search via Bitbucket API."""
import json, logging, os, re, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("bitbucket-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8516"))
mcp = FastMCP("Bitbucket MCP Server", instructions="Search Bitbucket code for emails and hostnames.")

@mcp.tool()
def bitbucket_code_search(query: str, limit: int = 50) -> str:
    """Search Bitbucket code and extract emails/hostnames.
    Args: query: Search term. limit: Max results."""
    try:
        r = httpx.get(f"https://api.bitbucket.org/2.0/search/code", params={"search_query": query, "pagelen": min(limit, 100)}, timeout=30)
        r.raise_for_status()
        text = r.text
        emails = sorted(set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)))
        hosts = sorted(set(re.findall(r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text)))[:100]
        return json.dumps({"query": query, "emails": emails, "hostnames": hosts}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting bitbucket-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
