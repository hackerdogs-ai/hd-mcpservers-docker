#!/usr/bin/env python3
"""Brave Search MCP Server — web search via Brave Search API."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("bravesearch-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8517"))
mcp = FastMCP("Brave Search MCP Server", instructions="Web search via Brave Search API.")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

@mcp.tool()
def brave_search(query: str, count: int = 20) -> str:
    """Search the web using Brave Search API.
    Args: query: Search query. count: Number of results (max 100)."""
    if not BRAVE_API_KEY: return json.dumps({"error": "BRAVE_API_KEY not set"})
    try:
        r = httpx.get("https://api.search.brave.com/res/v1/web/search", params={"q": query, "count": min(count, 100)}, headers={"X-Subscription-Token": BRAVE_API_KEY, "Accept": "application/json"}, timeout=30)
        r.raise_for_status()
        data = r.json()
        results = [{"title": w.get("title"), "url": w.get("url"), "description": w.get("description")} for w in data.get("web", {}).get("results", [])]
        return json.dumps({"query": query, "results": results, "count": len(results)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting bravesearch-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
