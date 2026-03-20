#!/usr/bin/env python3
"""Atlassian MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Atlassian MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-atlassian-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8404"))

mcp = FastMCP("Atlassian MCP Server", instructions="Integrates AI tools for Jira and Confluence tasks and automation. Model Context Protocol (MCP) server for Atlassian products (Confluence and")


@mcp.tool()
def acuvity_mcp_server_atlassian_info() -> str:
    """Return basic info / status for Atlassian MCP Server."""
    return "Atlassian MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-atlassian-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
