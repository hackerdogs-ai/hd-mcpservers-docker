#!/usr/bin/env python3
"""Browserless MCP Server — headless Chrome via Browserless API."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("browserless-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8518"))
mcp = FastMCP("Browserless MCP Server", instructions="Headless Chrome: content extraction, screenshots, PDFs via Browserless.")
BL_URL = os.environ.get("BROWSERLESS_URL", "http://localhost:3000")
BL_TOKEN = os.environ.get("BROWSERLESS_API_KEY", "")

def _bl_post(endpoint, payload):
    headers = {"Content-Type": "application/json"}
    if BL_TOKEN: headers["Authorization"] = f"Bearer {BL_TOKEN}"
    try:
        r = httpx.post(f"{BL_URL}{endpoint}", json=payload, headers=headers, timeout=60)
        r.raise_for_status()
        ct = r.headers.get("content-type", "")
        if "json" in ct: return json.dumps(r.json(), indent=2)
        return r.text[:5000] if "text" in ct else json.dumps({"status": "success", "content_type": ct, "size": len(r.content)})
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def browserless_content(url: str) -> str:
    """Get rendered HTML content from a URL.
    Args: url: URL to render."""
    return _bl_post("/content", {"url": url})

@mcp.tool()
def browserless_screenshot(url: str, full_page: bool = False) -> str:
    """Take a screenshot of a URL.
    Args: url: URL. full_page: Capture full page."""
    return _bl_post("/screenshot", {"url": url, "options": {"fullPage": full_page, "type": "png"}})

@mcp.tool()
def browserless_pdf(url: str) -> str:
    """Generate PDF from a URL.
    Args: url: URL to convert."""
    return _bl_post("/pdf", {"url": url})

@mcp.tool()
def browserless_scrape(url: str, selector: str = "body") -> str:
    """Scrape specific elements from a URL.
    Args: url: URL. selector: CSS selector."""
    return _bl_post("/scrape", {"url": url, "elements": [{"selector": selector}]})

if __name__ == "__main__":
    logger.info("Starting browserless-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
