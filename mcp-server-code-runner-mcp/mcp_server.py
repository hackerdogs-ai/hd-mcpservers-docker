#!/usr/bin/env python3
"""Code Runner MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Code Runner MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("mcp-server-code-runner-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8409"))

mcp = FastMCP("Code Runner MCP Server", instructions="MCP Server for running code snippet and show the result.  It supports running multiple programming languages: JavaScript")


@mcp.tool()
def mcp_server_code_runner_info() -> str:
    """Return basic info / status for Code Runner MCP Server."""
    return "Code Runner MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting mcp-server-code-runner-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
