#!/usr/bin/env python3
"""Wiremcp — MCP Server (upstream image wrapper).

Provides MCP access to Wiremcp via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("wiremcp-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8458"))

mcp = FastMCP("Wiremcp", instructions="A Model Context Protocol (MCP) server that connects AI assistants to Wireshark (via tshark) for real-time network traffic analysis. It empow")


@mcp.tool()
def wiremcp_info() -> str:
    """Return basic info / status for Wiremcp."""
    return "Wiremcp MCP server is running."


if __name__ == "__main__":
    logger.info("Starting wiremcp-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
