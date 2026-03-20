#!/usr/bin/env python3
"""Flights MCP — MCP Server (upstream image wrapper).

Provides MCP access to Flights MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("flights-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8422"))

mcp = FastMCP("Flights MCP", instructions="A Model Context Protocol (MCP) server that provides flight search capabilities by integrating with the Aviasales Flight Search API. It allow")


@mcp.tool()
def flights_info() -> str:
    """Return basic info / status for Flights MCP."""
    return "Flights MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting flights-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
