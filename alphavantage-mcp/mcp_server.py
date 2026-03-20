#!/usr/bin/env python3
"""Alpha Vantage MCP — MCP Server (upstream image wrapper).

Provides MCP access to Alpha Vantage MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("alphavantage-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8402"))

mcp = FastMCP("Alpha Vantage MCP", instructions="A Model Context Protocol (MCP) server providing real-time and historical financial data. It offers a standardized interface for stock quotes")


@mcp.tool()
def alphavantage_info() -> str:
    """Return basic info / status for Alpha Vantage MCP."""
    return "Alpha Vantage MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting alphavantage-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
