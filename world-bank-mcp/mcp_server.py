#!/usr/bin/env python3
"""World Bank MCP — MCP Server (upstream image wrapper).

Provides MCP access to World Bank MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("world-bank-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8459"))

mcp = FastMCP("World Bank MCP", instructions="A Model Context Protocol (MCP) server that enables interaction with the open World Bank data API. It allows AI assistants to access global e")


@mcp.tool()
def world_bank_info() -> str:
    """Return basic info / status for World Bank MCP."""
    return "World Bank MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting world-bank-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
