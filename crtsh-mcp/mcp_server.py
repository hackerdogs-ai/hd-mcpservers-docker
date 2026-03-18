#!/usr/bin/env python3
"""crt.sh MCP Server — discover subdomains from SSL certificate logs.

Uses the crt.sh API (no local binary). Supports stdio and streamable-http (no Minibridge).
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
logger = logging.getLogger("crtsh-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8381"))

mcp = FastMCP(
    "crt.sh MCP Server",
    instructions="Discover subdomains from SSL certificate logs via crt.sh.",
)

CRTSH_URL = "https://crt.sh/?q={query}&output=json"


def _parse_name_value(name_value: str) -> list[str]:
    return [v.strip() for v in name_value.split("\n") if v.strip()]


def _filter_subdomains(domains: list[str], base: str) -> list[str]:
    escaped = re.escape(base)
    pattern = re.compile(rf"^[^.]+\.{escaped}\b$")
    seen: set[str] = set()
    out: list[str] = []
    for d in domains:
        if d not in seen and pattern.match(d):
            seen.add(d)
            out.append(d)
    return out


async def _get_crtsh(target: str) -> list[str]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(CRTSH_URL.format(query=target))
        r.raise_for_status()
        data = r.json()
    all_domains: list[str] = []
    for item in data:
        name_value = item.get("name_value") or ""
        all_domains.extend(_parse_name_value(name_value))
    return _filter_subdomains(all_domains, target)


@mcp.tool()
async def crtsh(target: str) -> str:
    """Discover subdomains from SSL certificate logs (crt.sh).

    Args:
        target: Target domain (e.g. example.com).
    """
    logger.info("crtsh target=%s", target)
    try:
        domains = await _get_crtsh(target)
        return json.dumps(domains, indent=2)
    except Exception as e:
        logger.exception("crtsh failed")
        return json.dumps({"error": str(e)})


def main():
    logger.info("Starting crtsh-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
