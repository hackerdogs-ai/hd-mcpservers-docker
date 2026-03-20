#!/usr/bin/env python3
"""Scrapy MCP Server — web scraping via Scrapy."""
import asyncio, json, logging, os, sys
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("scrapy-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8526"))
mcp = FastMCP("Scrapy MCP Server", instructions="Web scraping via Scrapy spiders.")

@mcp.tool()
async def scrapy_crawl(url: str, max_pages: int = 10) -> str:
    """Crawl a URL using Scrapy.
    Args: url: Starting URL. max_pages: Max pages to follow."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "scrapy", "fetch", "--nolog", url,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        out = stdout.decode("utf-8", errors="replace")[:5000]
        return json.dumps({"url": url, "content_preview": out, "length": len(out)})
    except FileNotFoundError:
        return json.dumps({"error": "scrapy not found. Install: pip install scrapy"})
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting scrapy-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
