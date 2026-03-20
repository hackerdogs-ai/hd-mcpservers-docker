#!/usr/bin/env python3
"""FRED MCP SERVER — MCP Server (upstream image wrapper).

Provides MCP access to FRED MCP SERVER via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("fred-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8423"))

mcp = FastMCP("FRED MCP SERVER", instructions="A Model Context Protocol (MCP) server providing structured access to over 800")


@mcp.tool()
def fred_info() -> str:
    """Return basic info / status for FRED MCP SERVER."""
    return "FRED MCP SERVER MCP server is running."


if __name__ == "__main__":
    logger.info("Starting fred-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
