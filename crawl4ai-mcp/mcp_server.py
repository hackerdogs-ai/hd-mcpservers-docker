#!/usr/bin/env python3
"""Crawl4AI MCP Server — AI-powered web crawling."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("crawl4ai-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8521"))
mcp = FastMCP("Crawl4AI MCP Server", instructions="AI-powered web crawling via Crawl4AI.")
CRAWL4AI_URL = os.environ.get("CRAWL4AI_URL", "http://localhost:11235")
CRAWL4AI_TOKEN = os.environ.get("CRAWL4AI_API_TOKEN", "")

@mcp.tool()
def crawl4ai_crawl(url: str, css_selector: str = "", screenshot: bool = False) -> str:
    """Crawl a URL using Crawl4AI.
    Args: url: URL to crawl. css_selector: Optional CSS selector. screenshot: Take screenshot."""
    headers = {"Content-Type": "application/json"}
    if CRAWL4AI_TOKEN: headers["Authorization"] = f"Bearer {CRAWL4AI_TOKEN}"
    payload = {"urls": [url], "priority": 10}
    if css_selector: payload["css_selector"] = css_selector
    if screenshot: payload["screenshot"] = True
    try:
        r = httpx.post(f"{CRAWL4AI_URL}/crawl", json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        return json.dumps(r.json(), indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting crawl4ai-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
