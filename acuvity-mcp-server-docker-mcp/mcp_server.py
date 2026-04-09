#!/usr/bin/env python3
"""Docker MCP server — MCP Server (upstream image wrapper).

Provides MCP access to Docker MCP server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-docker-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8412"))

mcp = FastMCP("Docker MCP server", instructions="An MCP server for managing Docker with natural language!  What can it do? Compose containers with natural language Introspect & debug runnin")


@mcp.tool()
def acuvity_mcp_server_docker_info() -> str:
    """Return basic info / status for Docker MCP server."""
    return "Docker MCP server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-docker-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
