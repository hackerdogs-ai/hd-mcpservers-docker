#!/usr/bin/env python3
"""BuiltWith MCP Server — domain technology stack lookup via BuiltWith API.

Uses BuiltWith Domain API v22. Requires BUILTWITH_API_KEY (https://builtwith.com/).
"""

import json
import logging
import os
import re
import sys

import httpx
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("builtwith-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8375"))

mcp = FastMCP(
    "BuiltWith MCP Server",
    instructions="Domain technology lookup via BuiltWith API. Use domain_lookup for a single domain. Requires BUILTWITH_API_KEY.",
)

BUILTWITH_API_KEY = os.environ.get("BUILTWITH_API_KEY", "")
API_BASE = "https://api.builtwith.com/v22"


def _normalize_domain(domain: str) -> str:
    """Strip protocol and path, lowercase."""
    s = (domain or "").strip().lower()
    s = re.sub(r"^https?://", "", s)
    s = re.sub(r"/.*$", "", s)
    return s or ""


@mcp.tool()
def domain_lookup(domain: str) -> str:
    """Get technology stack for a domain (e.g. example.com). Returns technologies, paths, and meta from BuiltWith."""
    dom = _normalize_domain(domain)
    if not dom:
        return json.dumps({"error": "domain is required"})
    if not BUILTWITH_API_KEY:
        return json.dumps({"error": "BUILTWITH_API_KEY is not set"})
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                f"{API_BASE}/api.json",
                params={"KEY": BUILTWITH_API_KEY, "LOOKUP": dom},
            )
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "body": (e.response.text or "")[:500]})
    except Exception as e:
        logger.exception("domain_lookup failed")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting builtwith-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
