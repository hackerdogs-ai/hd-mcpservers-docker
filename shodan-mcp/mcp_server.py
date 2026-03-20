#!/usr/bin/env python3
"""Shodan MCP — MCP Server (upstream image wrapper).

Provides MCP access to Shodan MCP via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("shodan-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8453"))

mcp = FastMCP("Shodan MCP", instructions="A dual-purpose cybersecurity server that combines Shodan’s internet-scale device intelligence with VirusTotal’s reputation analysis. It allo")


@mcp.tool()
def shodan_info() -> str:
    """Return basic info / status for Shodan MCP."""
    return "Shodan MCP MCP server is running."


if __name__ == "__main__":
    logger.info("Starting shodan-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
