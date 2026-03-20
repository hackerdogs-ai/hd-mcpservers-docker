#!/usr/bin/env python3
"""DuckDuckGo Search MCP Server (Acuvity) — MCP Server (upstream image wrapper).

Provides MCP access to DuckDuckGo Search MCP Server (Acuvity) via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-duckduckgo-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8414"))

mcp = FastMCP("DuckDuckGo Search MCP Server (Acuvity)", instructions="A Model Context Protocol (MCP) server that provides web search capabilities through DuckDuckGo")


@mcp.tool()
def acuvity_mcp_server_duckduckgo_info() -> str:
    """Return basic info / status for DuckDuckGo Search MCP Server (Acuvity)."""
    return "DuckDuckGo Search MCP Server (Acuvity) MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-duckduckgo-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
