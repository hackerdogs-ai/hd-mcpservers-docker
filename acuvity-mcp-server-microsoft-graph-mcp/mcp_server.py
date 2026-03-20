#!/usr/bin/env python3
"""Microsoft Graph MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Microsoft Graph MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-microsoft-graph-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8433"))

mcp = FastMCP("Microsoft Graph MCP Server", instructions="Connect to microsoft graph API to get applications")


@mcp.tool()
def acuvity_mcp_server_microsoft_graph_info() -> str:
    """Return basic info / status for Microsoft Graph MCP Server."""
    return "Microsoft Graph MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-microsoft-graph-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
