#!/usr/bin/env python3
"""DuckDuckGo MCP server — MCP Server (upstream image wrapper).

Provides MCP access to DuckDuckGo MCP server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("duckduckgo-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8413"))

mcp = FastMCP("DuckDuckGo MCP server", instructions="A Model Context Protocol (MCP) server that provides web search capabilities through DuckDuckGo")


@mcp.tool()
def duckduckgo_info() -> str:
    """Return basic info / status for DuckDuckGo MCP server."""
    return "DuckDuckGo MCP server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting duckduckgo-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
