#!/usr/bin/env python3
"""Scrapezy MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Scrapezy MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-scrapezy-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8450"))

mcp = FastMCP("Scrapezy MCP Server", instructions="A Model Context Protocol server for Scrapezy that enables AI models to extract structured data from websites.  Features Tools extract_struct")


@mcp.tool()
def acuvity_mcp_server_scrapezy_info() -> str:
    """Return basic info / status for Scrapezy MCP Server."""
    return "Scrapezy MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-scrapezy-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
