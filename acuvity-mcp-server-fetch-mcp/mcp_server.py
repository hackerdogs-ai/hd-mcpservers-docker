#!/usr/bin/env python3
"""Fetch Mcp Server — MCP Server (upstream image wrapper).

Provides MCP access to Fetch Mcp Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-fetch-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8419"))

mcp = FastMCP("Fetch Mcp Server", instructions="Fetch MCP Server A Model Context Protocol server that provides web content fetching capabilities. This server enables LLMs to retrieve and p")


@mcp.tool()
def acuvity_mcp_server_fetch_info() -> str:
    """Return basic info / status for Fetch Mcp Server."""
    return "Fetch Mcp Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-fetch-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
