#!/usr/bin/env python3
"""Financial Datasets MCP — MCP Server (upstream image wrapper).

Provides MCP access to Financial Datasets MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("financial-datasets-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8420"))

mcp = FastMCP("Financial Datasets MCP", instructions="A comprehensive financial data server that connects AI assistants to real-time and historical stock market intelligence. It provides specifi")


@mcp.tool()
def financial_datasets_info() -> str:
    """Return basic info / status for Financial Datasets MCP."""
    return "Financial Datasets MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting financial-datasets-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
