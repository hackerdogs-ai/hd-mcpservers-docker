#!/usr/bin/env python3
"""Edgar Tools MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Edgar Tools MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("edgartools-mcp-server-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8415"))

mcp = FastMCP("Edgar Tools MCP Server", instructions="EdgarTools supports all SEC form types including 10-K annual reports")


@mcp.tool()
def edgartools_mcp_server_info() -> str:
    """Return basic info / status for Edgar Tools MCP Server."""
    return "Edgar Tools MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting edgartools-mcp-server-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
