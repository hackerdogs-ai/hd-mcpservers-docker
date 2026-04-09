#!/usr/bin/env python3
"""RSS MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to RSS MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("rss-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8448"))

mcp = FastMCP("RSS MCP Server", instructions="This is a Model Context Protocol (MCP) server built with TypeScript. It provides a versatile tool to fetch and parse any standard RSS/Atom f")


@mcp.tool()
def rss_info() -> str:
    """Return basic info / status for RSS MCP Server."""
    return "RSS MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting rss-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
