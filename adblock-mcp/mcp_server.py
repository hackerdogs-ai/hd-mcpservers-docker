#!/usr/bin/env python3
"""Adblock MCP Server — check URLs against AdBlock Plus blocklists."""
import json, logging, os, sys
import httpx
from fastmcp import FastMCP
try:
    from adblockparser import AdblockRules
    ABP_AVAILABLE = True
except ImportError:
    ABP_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("adblock-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8508"))
mcp = FastMCP("Adblock MCP Server", instructions="Check URLs against AdBlock Plus compatible blocklists (EasyList).")

_rules_cache = {}

def _get_rules(blocklist_url: str = "https://easylist-downloads.adblockplus.org/easylist.txt") -> "AdblockRules":
    if blocklist_url in _rules_cache:
        return _rules_cache[blocklist_url]
    r = httpx.get(blocklist_url, timeout=30, follow_redirects=True)
    lines = [l for l in r.text.splitlines() if l and not l.startswith("!") and not l.startswith("[")]
    rules = AdblockRules(lines)
    _rules_cache[blocklist_url] = rules
    return rules

@mcp.tool()
def adblock_check_url(url: str, blocklist_url: str = "https://easylist-downloads.adblockplus.org/easylist.txt") -> str:
    """Check if a URL would be blocked by AdBlock Plus rules.
    Args:
        url: URL to check.
        blocklist_url: Blocklist URL (default: EasyList).
    """
    if not ABP_AVAILABLE:
        return json.dumps({"error": "adblockparser not installed"})
    try:
        rules = _get_rules(blocklist_url)
        blocked = rules.should_block(url)
        return json.dumps({"url": url, "blocked": blocked}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting adblock-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
