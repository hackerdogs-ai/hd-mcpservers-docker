#!/usr/bin/env python3
"""Bing Search MCP server — MCP Server (upstream image wrapper).

Provides MCP access to Bing Search MCP server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-bing-search-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8405"))

mcp = FastMCP("Bing Search MCP server", instructions="A Model Context Protocol (MCP) server for Microsoft Bing Search API integration")


@mcp.tool()
def acuvity_mcp_server_bing_search_info() -> str:
    """Return basic info / status for Bing Search MCP server."""
    return "Bing Search MCP server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-bing-search-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
