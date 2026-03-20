#!/usr/bin/env python3
"""Minio AIStor MCP Server (Official) — MCP Server (upstream image wrapper).

Provides MCP access to Minio AIStor MCP Server (Official) via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("aistor-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8434"))

mcp = FastMCP("Minio AIStor MCP Server (Official)", instructions="The official Model Context Protocol server for MinIO’s exabyte-scale object storage. It provides AI agents with a natural language interface")


@mcp.tool()
def aistor_info() -> str:
    """Return basic info / status for Minio AIStor MCP Server (Official)."""
    return "Minio AIStor MCP Server (Official) MCP server is running."


if __name__ == "__main__":
    logger.info("Starting aistor-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
