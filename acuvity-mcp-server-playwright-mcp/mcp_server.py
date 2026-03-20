#!/usr/bin/env python3
"""Playwright MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Playwright MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-playwright-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8444"))

mcp = FastMCP("Playwright MCP Server", instructions="A Model Context Protocol (MCP) server that provides browser automation capabilities using Playwright. This server enables LLMs to interact w")


@mcp.tool()
def acuvity_mcp_server_playwright_info() -> str:
    """Return basic info / status for Playwright MCP Server."""
    return "Playwright MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-playwright-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
