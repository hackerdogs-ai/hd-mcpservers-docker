#!/usr/bin/env python3
"""OpenCV MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to OpenCV MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("opencv-mcp-server-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8440"))

mcp = FastMCP("OpenCV MCP Server", instructions="OpenCV MCP Server is a Python package that provides OpenCV's image and video processing capabilities through the Model Context Protocol (MCP")


@mcp.tool()
def opencv_mcp_server_info() -> str:
    """Return basic info / status for OpenCV MCP Server."""
    return "OpenCV MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting opencv-mcp-server-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
