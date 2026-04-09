#!/usr/bin/env python3
"""AbuseIPDB MCP Server — IP reputation and abuse checks.

Wraps the AbuseIPDB API for IP reputation lookups via the Model Context Protocol.
Requires ABUSEIPDB_API_KEY (https://www.abuseipdb.com/).
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
logger = logging.getLogger("abuseipdb-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8374"))

mcp = FastMCP(
    "AbuseIPDB MCP Server",
    instructions="IP reputation and abuse checks via AbuseIPDB API. Requires ABUSEIPDB_API_KEY.",
)

ABUSEIPDB_API_KEY = os.environ.get("ABUSEIPDB_API_KEY", "")
API_URL = "https://api.abuseipdb.com/api/v2/check"


@mcp.tool()
def check_ip(ip_address: str, max_age_days: int = 90) -> str:
    """Check an IP address against AbuseIPDB. Returns abuse score, country, reports, etc."""
    if not ip_address or not ip_address.strip():
        return json.dumps({"error": "ip_address is required"})
    if not ABUSEIPDB_API_KEY:
        return json.dumps({"error": "ABUSEIPDB_API_KEY is not set"})
    if max_age_days < 1:
        max_age_days = 1
    if max_age_days > 365:
        max_age_days = 365
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.get(
                API_URL,
                params={"ipAddress": ip_address.strip(), "maxAgeInDays": max_age_days},
                headers={"Key": ABUSEIPDB_API_KEY, "Accept": "application/json"},
            )
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "body": e.response.text[:500]})
    except Exception as e:
        logger.exception("check_ip failed")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting abuseipdb-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
