#!/usr/bin/env python3
"""Scan URL MCP server — MCP Server (upstream image wrapper).

Provides MCP access to Scan URL MCP server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("scan-url-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8449"))

mcp = FastMCP("Scan URL MCP server", instructions="An enhanced security reconnaissance server that integrates with the urlscan.io API. It enables AI assistants to perform deep web analysis an")


@mcp.tool()
def scan_url_info() -> str:
    """Return basic info / status for Scan URL MCP server."""
    return "Scan URL MCP server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting scan-url-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
