#!/usr/bin/env python3
"""Chroma MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Chroma MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-chroma-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8408"))

mcp = FastMCP("Chroma MCP Server", instructions="This server provides data retrieval capabilities powered by Chroma vector database")


@mcp.tool()
def acuvity_mcp_server_chroma_info() -> str:
    """Return basic info / status for Chroma MCP Server."""
    return "Chroma MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-chroma-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
