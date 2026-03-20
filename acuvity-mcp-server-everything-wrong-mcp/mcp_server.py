#!/usr/bin/env python3
"""Everything Wrong MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Everything Wrong MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-everything-wrong-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8418"))

mcp = FastMCP("Everything Wrong MCP Server", instructions="A demonstration Model Context Protocol (MCP) server that exposes a variety of “tools”—some benign")


@mcp.tool()
def acuvity_mcp_server_everything_wrong_info() -> str:
    """Return basic info / status for Everything Wrong MCP Server."""
    return "Everything Wrong MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-everything-wrong-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
