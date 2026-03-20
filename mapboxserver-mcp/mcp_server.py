#!/usr/bin/env python3
"""Mapbox MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Mapbox MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("mapboxserver-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8429"))

mcp = FastMCP("Mapbox MCP Server", instructions="The Mapbox MCP Server transforms any AI agent or application into a geospatially-aware system by providing seamless access to Mapbox's compr")


@mcp.tool()
def mapboxserver_info() -> str:
    """Return basic info / status for Mapbox MCP Server."""
    return "Mapbox MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting mapboxserver-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
