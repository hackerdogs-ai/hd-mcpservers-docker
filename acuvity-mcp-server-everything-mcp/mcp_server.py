#!/usr/bin/env python3
"""MCP Server Everything — MCP Server (upstream image wrapper).

Provides MCP access to MCP Server Everything via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-everything-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8431"))

mcp = FastMCP("MCP Server Everything", instructions="MCP server that exercises all the features of the MCP protocol")


@mcp.tool()
def acuvity_mcp_server_everything_info() -> str:
    """Return basic info / status for MCP Server Everything."""
    return "MCP Server Everything MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-everything-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
