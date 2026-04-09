#!/usr/bin/env python3
"""Arjun MCP Server — MCP wrapper server.

Provides MCP protocol compliance (stdio + streamable-http) for Arjun-based
hidden parameter discovery workflows in a lightweight, Hackerdogs-ready container.
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
logger = logging.getLogger("acuvity-mcp-server-arjun-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8382"))

mcp = FastMCP(
    "Arjun MCP Server",
    instructions="HTTP parameter discovery (hidden GET/POST parameters) for web security testing workflows.",
)


@mcp.tool()
def acuvity_mcp_server_arjun_info() -> str:
    return "Arjun MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-arjun-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
