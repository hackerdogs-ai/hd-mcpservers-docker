#!/usr/bin/env python3
"""Crunchbase MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Crunchbase MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("crunchbase-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8411"))

mcp = FastMCP("Crunchbase MCP Server", instructions="A Model Context Protocol (MCP) server that connects AI assistants to Crunchbase data. It enables users to search for companies")


@mcp.tool()
def crunchbase_info() -> str:
    """Return basic info / status for Crunchbase MCP Server."""
    return "Crunchbase MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting crunchbase-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
