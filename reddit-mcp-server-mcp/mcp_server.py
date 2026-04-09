#!/usr/bin/env python3
"""Reddit MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Reddit MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("reddit-mcp-server-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8447"))

mcp = FastMCP("Reddit MCP Server", instructions="A comprehensive Model Context Protocol (MCP) server for Reddit integration. This server enables AI agents to interact with Reddit programmat")


@mcp.tool()
def reddit_mcp_server_info() -> str:
    """Return basic info / status for Reddit MCP Server."""
    return "Reddit MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting reddit-mcp-server-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
