#!/usr/bin/env python3
"""Amass MCP Server — MCP wrapper server.

Provides MCP protocol compliance (stdio + streamable-http) for Amass-based
recon workflows in a lightweight, Hackerdogs-ready container.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("acuvity-mcp-server-amass-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8381"))

mcp = FastMCP(
    "Amass MCP Server",
    instructions="Subdomain reconnaissance (intel, enum, viz, track) for enumeration workflows.",
)


@mcp.tool()
def acuvity_mcp_server_amass_info() -> str:
    return "Amass MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-amass-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
