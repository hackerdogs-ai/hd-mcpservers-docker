#!/usr/bin/env python3
"""Slack MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Slack MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("slack-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8454"))

mcp = FastMCP("Slack MCP Server", instructions="A specialized communication server for Slack that operates in a ""Stealth Mode")


@mcp.tool()
def slack_info() -> str:
    """Return basic info / status for Slack MCP Server."""
    return "Slack MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting slack-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
