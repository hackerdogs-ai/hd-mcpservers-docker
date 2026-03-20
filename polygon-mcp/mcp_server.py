#!/usr/bin/env python3
"""Polygon MCP server — MCP Server (upstream image wrapper).

Provides MCP access to Polygon MCP server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("polygon-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8445"))

mcp = FastMCP("Polygon MCP server", instructions="Polygon MCP Server A Model Context Protocol (MCP) server that provides tools for interacting with the Polygon.io API for market data. A fina")


@mcp.tool()
def polygon_info() -> str:
    """Return basic info / status for Polygon MCP server."""
    return "Polygon MCP server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting polygon-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
