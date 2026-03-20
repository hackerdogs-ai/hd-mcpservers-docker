#!/usr/bin/env python3
"""AdGuard DNS MCP Server — check if hosts are blocked by AdGuard DNS."""
import json, logging, os, socket, sys
from fastmcp import FastMCP
try:
    import dns.resolver
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("adguard-dns-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8509"))
mcp = FastMCP("AdGuard DNS MCP Server", instructions="Check if hosts are blocked by AdGuard DNS filtering.")

ADGUARD_DEFAULT = "94.140.14.14"
ADGUARD_FAMILY = "94.140.15.15"
BLOCKED_IP = "94.140.14.35"

@mcp.tool()
def adguard_dns_check(host: str, mode: str = "default") -> str:
    """Check if a host is blocked by AdGuard DNS.
    Args:
        host: Hostname to check.
        mode: 'default', 'family', or 'both'.
    """
    if not DNS_AVAILABLE:
        return json.dumps({"error": "dnspython not installed"})
    results = {}
    servers = []
    if mode in ("default", "both"): servers.append(("default", ADGUARD_DEFAULT))
    if mode in ("family", "both"): servers.append(("family", ADGUARD_FAMILY))
    if not servers: servers = [("default", ADGUARD_DEFAULT)]
    for name, server in servers:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [server]
            resolver.timeout = 5
            resolver.lifetime = 5
            answers = resolver.resolve(host, "A")
            ips = [str(a) for a in answers]
            results[name] = {"ips": ips, "blocked": BLOCKED_IP in ips}
        except Exception as e:
            results[name] = {"error": str(e), "blocked": None}
    blocked_any = any(r.get("blocked") for r in results.values())
    return json.dumps({"host": host, "blocked": blocked_any, "results": results}, indent=2)

if __name__ == "__main__":
    logger.info("Starting adguard-dns-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
