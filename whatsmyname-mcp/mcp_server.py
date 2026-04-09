#!/usr/bin/env python3
"""WhatsMyName MCP Server — username enumeration across sites."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("whatsmyname-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8528"))
mcp = FastMCP("WhatsMyName MCP Server", instructions="Check username presence across websites using WhatsMyName dataset.")
WMN_URL = os.environ.get("WMN_DATA_URL", "https://raw.githubusercontent.com/WebBreacher/WhatsMyName/main/wmn-data.json")

@mcp.tool()
def whatsmyname_check(username: str, limit: int = 50) -> str:
    """Check if a username exists on various sites.
    Args: username: Username to search. limit: Max sites to check."""
    try:
        r = httpx.get(WMN_URL, timeout=30)
        r.raise_for_status()
        sites = r.json().get("sites", [])[:limit]
        found = []
        with httpx.Client(timeout=10, follow_redirects=True) as client:
            for site in sites:
                url = site.get("uri_check", "").replace("{account}", username)
                if not url: continue
                try:
                    resp = client.get(url, headers={"User-Agent": "wmn-mcp/1.0"})
                    check = site.get("e_string", "")
                    if check and check in resp.text:
                        found.append({"site": site.get("name", ""), "url": url, "category": site.get("cat", "")})
                except: pass
        return json.dumps({"username": username, "found": found, "count": len(found), "sites_checked": len(sites)}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting whatsmyname-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
