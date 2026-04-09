#!/usr/bin/env python3
"""OSHP MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to OSHP MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-oshp-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8441"))

mcp = FastMCP("OSHP MCP Server", instructions="Analyzes HTTP response headers against OWASP security standards with recommendations  The OWASP Secure Headers Project (OSHP) provides infor")


@mcp.tool()
def acuvity_mcp_server_oshp_info() -> str:
    """Return basic info / status for OSHP MCP Server."""
    return "OSHP MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-oshp-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
