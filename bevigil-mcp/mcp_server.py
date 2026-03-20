#!/usr/bin/env python3
"""BeVigil MCP Server — mobile app OSINT via BeVigil API."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("bevigil-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8515"))
mcp = FastMCP("BeVigil MCP Server", instructions="Mobile app OSINT: subdomains and URLs from BeVigil.")
BEVIGIL_API_KEY = os.environ.get("BEVIGIL_API_KEY", "")

@mcp.tool()
def bevigil_domain_osint(domain: str) -> str:
    """Get subdomains and URLs for a domain from BeVigil mobile app OSINT.
    Args: domain: Target domain."""
    if not BEVIGIL_API_KEY: return json.dumps({"error": "BEVIGIL_API_KEY not set"})
    headers = {"X-Access-Token": BEVIGIL_API_KEY}
    result = {"domain": domain}
    try:
        r = httpx.get(f"https://osint.bevigil.com/api/{domain}/subdomains/", headers=headers, timeout=30)
        result["subdomains"] = r.json().get("subdomains", []) if r.status_code == 200 else []
    except: result["subdomains"] = []
    try:
        r = httpx.get(f"https://osint.bevigil.com/api/{domain}/urls/", headers=headers, timeout=30)
        result["urls"] = r.json().get("urls", []) if r.status_code == 200 else []
    except: result["urls"] = []
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    logger.info("Starting bevigil-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
