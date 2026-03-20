#!/usr/bin/env python3
"""Cloud Datacenter MCP Server — identify IPs belonging to cloud providers."""
import ipaddress, json, logging, os, sys
import httpx
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("cloud-datacenter-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8520"))
mcp = FastMCP("Cloud Datacenter MCP Server", instructions="Identify if IPs belong to AWS, Azure, GCP, Cloudflare, or other cloud providers.")

FEEDS = {
    "aws": "https://ip-ranges.amazonaws.com/ip-ranges.json",
    "azure": "https://download.microsoft.com/download/7/1/D/71D86715-5596-4529-9B13-DA13A5DE5B63/ServiceTags_Public_20240101.json",
    "gcp": "https://www.gstatic.com/ipranges/cloud.json",
    "cloudflare": "https://www.cloudflare.com/ips-v4",
}

@mcp.tool()
def cloud_lookup_ip(ip: str) -> str:
    """Check if an IP belongs to a known cloud provider (AWS, GCP, Cloudflare).
    Args: ip: IPv4 or IPv6 address."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    matches = []
    try:
        r = httpx.get(FEEDS["aws"], timeout=15)
        for p in r.json().get("prefixes", []):
            if addr in ipaddress.ip_network(p["ip_prefix"], strict=False):
                matches.append({"provider": "AWS", "region": p.get("region"), "service": p.get("service"), "cidr": p["ip_prefix"]})
    except: pass
    try:
        r = httpx.get(FEEDS["gcp"], timeout=15)
        for p in r.json().get("prefixes", []):
            cidr = p.get("ipv4Prefix") or p.get("ipv6Prefix")
            if cidr and addr in ipaddress.ip_network(cidr, strict=False):
                matches.append({"provider": "GCP", "scope": p.get("scope"), "service": p.get("service"), "cidr": cidr})
    except: pass
    try:
        r = httpx.get(FEEDS["cloudflare"], timeout=15)
        for line in r.text.strip().splitlines():
            if addr in ipaddress.ip_network(line.strip(), strict=False):
                matches.append({"provider": "Cloudflare", "cidr": line.strip()})
    except: pass
    return json.dumps({"ip": ip, "matches": matches, "is_cloud": len(matches) > 0}, indent=2)

if __name__ == "__main__":
    logger.info("Starting cloud-datacenter-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
