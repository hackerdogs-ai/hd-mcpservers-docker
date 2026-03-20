#!/usr/bin/env python3
"""Cortex MCP server — MCP Server (upstream image wrapper).

Provides MCP access to Cortex MCP server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("cortex-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8410"))

mcp = FastMCP("Cortex MCP server", instructions="A security orchestration server that provides a unified interface for multiple threat intelligence analyzers. It allows AI agents to submit ")


@mcp.tool()
def cortex_info() -> str:
    """Return basic info / status for Cortex MCP server."""
    return "Cortex MCP server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting cortex-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
