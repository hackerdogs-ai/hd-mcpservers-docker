#!/usr/bin/env python3
"""Open Legal Compliance MCP — MCP Server (upstream image wrapper).

Provides MCP access to Open Legal Compliance MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("open-legal-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8439"))

mcp = FastMCP("Open Legal Compliance MCP", instructions="Based on the README.md for the repository TCoder920x/open-legal-compliance-mcp")


@mcp.tool()
def open_legal_info() -> str:
    """Return basic info / status for Open Legal Compliance MCP."""
    return "Open Legal Compliance MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting open-legal-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
