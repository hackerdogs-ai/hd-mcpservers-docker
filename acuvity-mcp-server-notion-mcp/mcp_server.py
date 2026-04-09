#!/usr/bin/env python3
"""Notion MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Notion MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-notion-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8437"))

mcp = FastMCP("Notion MCP Server", instructions="Notion MCP is our hosted server that gives AI tools secure access to your Notion workspace.  Generate documentation — Generate PRDs")


@mcp.tool()
def acuvity_mcp_server_notion_info() -> str:
    """Return basic info / status for Notion MCP Server."""
    return "Notion MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-notion-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
