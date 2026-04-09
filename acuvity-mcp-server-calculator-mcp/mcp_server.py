#!/usr/bin/env python3
"""Calculator MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Calculator MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-calculator-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8407"))

mcp = FastMCP("Calculator MCP Server", instructions="A Model Context Protocol server for calculating. This server enables LLMs to use calculator for precise numerical calculations.  Available T")


@mcp.tool()
def acuvity_mcp_server_calculator_info() -> str:
    """Return basic info / status for Calculator MCP Server."""
    return "Calculator MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-calculator-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
