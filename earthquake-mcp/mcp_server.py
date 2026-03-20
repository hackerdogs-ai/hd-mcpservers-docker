#!/usr/bin/env python3
"""USGS MCP — MCP Server (upstream image wrapper).

Provides MCP access to USGS MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("earthquake-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8457"))

mcp = FastMCP("USGS MCP", instructions="A comprehensive Model Context Protocol (MCP) server that integrates data from IRIS")


@mcp.tool()
def earthquake_info() -> str:
    """Return basic info / status for USGS MCP."""
    return "USGS MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting earthquake-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
