#!/usr/bin/env python3
"""PubMed MCP — MCP Server (upstream image wrapper).

Provides MCP access to PubMed MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("pubmed-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8446"))

mcp = FastMCP("PubMed MCP", instructions="A Model Context Protocol (MCP) server that enables AI assistants to search and analyze PubMed medical literature with advanced filtering")


@mcp.tool()
def pubmed_info() -> str:
    """Return basic info / status for PubMed MCP."""
    return "PubMed MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting pubmed-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
