#!/usr/bin/env python3
"""SEC Edgar MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to SEC Edgar MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("sec-edgar-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8451"))

mcp = FastMCP("SEC Edgar MCP Server", instructions="MCP server for accessing SEC EDGAR filings. Connects AI assistants to company filings")


@mcp.tool()
def sec_edgar_info() -> str:
    """Return basic info / status for SEC Edgar MCP Server."""
    return "SEC Edgar MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting sec-edgar-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
