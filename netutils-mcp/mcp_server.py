#!/usr/bin/env python3
"""NetUtils — MCP Server (upstream image wrapper).

Provides MCP access to NetUtils via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("netutils-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8436"))

mcp = FastMCP("NetUtils", instructions="A comprehensive network and domain analysis toolkit for AI assistants. It provides a suite of tools for DNS exploration (A")


@mcp.tool()
def netutils_info() -> str:
    """Return basic info / status for NetUtils."""
    return "NetUtils MCP server is running."


if __name__ == "__main__":
    logger.info("Starting netutils-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
