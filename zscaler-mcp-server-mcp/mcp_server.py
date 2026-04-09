#!/usr/bin/env python3
"""Zscaler MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Zscaler MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("zscaler-mcp-server-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8463"))

mcp = FastMCP("Zscaler MCP Server", instructions="The Zscaler MCP Server brings comprehensive Zscaler management capabilities directly to your AI agents and automation workflows. This compre")


@mcp.tool()
def zscaler_mcp_server_info() -> str:
    """Return basic info / status for Zscaler MCP Server."""
    return "Zscaler MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting zscaler-mcp-server-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
