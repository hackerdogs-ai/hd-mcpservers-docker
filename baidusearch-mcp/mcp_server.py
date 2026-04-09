#!/usr/bin/env python3
"""Baidu Search MCP Server — search Baidu and extract results."""
import json, logging, os, re, sys
import httpx
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("baidusearch-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8514"))
mcp = FastMCP("Baidu Search MCP Server", instructions="Search Baidu and extract emails/hostnames from results.")

@mcp.tool()
def baidu_search(query: str, limit: int = 50) -> str:
    """Search Baidu and extract emails and hostnames from results.
    Args:
        query: Search query.
        limit: Max result pages to fetch.
    """
    try:
        all_emails = set()
        all_hosts = set()
        for page in range(0, min(limit, 10)):
            r = httpx.get("https://www.baidu.com/s", params={"wd": query, "pn": page * 10}, timeout=15, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True)
            text = r.text
            all_emails.update(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text))
            all_hosts.update(re.findall(r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text))
        return json.dumps({"query": query, "emails": sorted(all_emails), "hostnames": sorted(all_hosts)[:100]}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting baidusearch-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
