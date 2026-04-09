#!/usr/bin/env python3
"""Atlas Docs MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Atlas Docs MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-atlas-docs-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8403"))

mcp = FastMCP("Atlas Docs MCP Server", instructions="Atlas Docs MCP server:  Provides technical documentation for libraries and frameworks Processes the official docs into a clean markdown vers")


@mcp.tool()
def acuvity_mcp_server_atlas_docs_info() -> str:
    """Return basic info / status for Atlas Docs MCP Server."""
    return "Atlas Docs MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-atlas-docs-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
