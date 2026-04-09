#!/usr/bin/env python3
"""Yahoo Finance MCP SERVER — MCP Server (upstream image wrapper).

Provides MCP access to Yahoo Finance MCP SERVER via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("yfmcp-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8460"))

mcp = FastMCP("Yahoo Finance MCP SERVER", instructions="Yahoo Finance MCP Server A simple MCP server for Yahoo Finance using yfinance. This server provides a set of tools to fetch stock data")


@mcp.tool()
def yfmcp_info() -> str:
    """Return basic info / status for Yahoo Finance MCP SERVER."""
    return "Yahoo Finance MCP SERVER MCP server is running."


if __name__ == "__main__":
    logger.info("Starting yfmcp-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
