#!/usr/bin/env python3
"""PageSpeed MCP Server — Google PageSpeed Insights.

Calls the PageSpeed Insights API (v5). Optional PAGESPEED_API_KEY for higher quota.
"""

import json
import logging
import os
import sys
import httpx
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("pagespeed-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8378"))

mcp = FastMCP(
    "PageSpeed MCP Server",
    instructions="Run Google PageSpeed Insights on a URL. Use run_pagespeed for desktop and/or mobile. Optional PAGESPEED_API_KEY for higher quota.",
)

PAGESPEED_API_KEY = os.environ.get("PAGESPEED_API_KEY", "")
API_BASE = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


@mcp.tool()
def run_pagespeed(
    url: str,
    strategy: str = "mobile",
    categories: str | None = None,
) -> str:
    """Run PageSpeed Insights on a URL. strategy: 'mobile' or 'desktop'. categories: comma-separated PERFORMANCE,ACCESSIBILITY,SEO,BEST_PRACTICES (default all)."""
    if not url or not url.strip():
        return json.dumps({"error": "url is required"})
    if strategy not in ("mobile", "desktop"):
        strategy = "mobile"
    try:
        params = {"url": url.strip(), "strategy": strategy}
        if PAGESPEED_API_KEY:
            params["key"] = PAGESPEED_API_KEY
        if categories and categories.strip():
            params["category"] = [c.strip() for c in categories.split(",") if c.strip()]
        with httpx.Client(timeout=60.0) as client:
            r = client.get(API_BASE, params=params)
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "body": (e.response.text or "")[:500]})
    except Exception as e:
        logger.exception("run_pagespeed failed")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting pagespeed-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
