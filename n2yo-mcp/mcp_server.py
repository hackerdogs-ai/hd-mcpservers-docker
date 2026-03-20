#!/usr/bin/env python3
"""N2YO MCP — MCP Server (upstream image wrapper).

Provides MCP access to N2YO MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("n2yo-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8435"))

mcp = FastMCP("N2YO MCP", instructions="A Model Context Protocol (MCP) server that connects AI assistants to the N2YO.com API for real-time satellite tracking. It enables users to ")


@mcp.tool()
def n2yo_info() -> str:
    """Return basic info / status for N2YO MCP."""
    return "N2YO MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting n2yo-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
