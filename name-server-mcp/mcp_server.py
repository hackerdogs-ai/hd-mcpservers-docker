#!/usr/bin/env python3
"""Name Server MCP Server — public DNS resolver lookups."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("name-server-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8525"))
mcp = FastMCP("Name Server MCP Server", instructions="Look up IPs in public DNS resolver lists.")

@mcp.tool()
def nameserver_check_ip(ip: str) -> str:
    """Check if an IP is a known public DNS resolver.
    Args: ip: IP address to check."""
    known = {"8.8.8.8": "Google", "8.8.4.4": "Google", "1.1.1.1": "Cloudflare", "1.0.0.1": "Cloudflare",
             "9.9.9.9": "Quad9", "149.112.112.112": "Quad9", "208.67.222.222": "OpenDNS", "208.67.220.220": "OpenDNS",
             "94.140.14.14": "AdGuard", "94.140.15.15": "AdGuard"}
    provider = known.get(ip)
    return json.dumps({"ip": ip, "is_public_resolver": provider is not None, "provider": provider}, indent=2)

if __name__ == "__main__":
    logger.info("Starting name-server-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
