#!/usr/bin/env python3
"""Marine Traffic MCP — MCP Server (upstream image wrapper).

Provides MCP access to Marine Traffic MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("marinetraffic-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8430"))

mcp = FastMCP("Marine Traffic MCP", instructions="A Model Context Protocol (MCP) server that connects AI assistants to the MarineTraffic API. It provides real-time vessel tracking")


@mcp.tool()
def marinetraffic_info() -> str:
    """Return basic info / status for Marine Traffic MCP."""
    return "Marine Traffic MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting marinetraffic-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
