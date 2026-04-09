#!/usr/bin/env python3
"""Microsoft Azure MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Microsoft Azure MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-azure-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8432"))

mcp = FastMCP("Microsoft Azure MCP Server", instructions="Integrates AI agents with Azure services for enhanced functionality.")


@mcp.tool()
def acuvity_mcp_server_azure_info() -> str:
    """Return basic info / status for Microsoft Azure MCP Server."""
    return "Microsoft Azure MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-azure-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
