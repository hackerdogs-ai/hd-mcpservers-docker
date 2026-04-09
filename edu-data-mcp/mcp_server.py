#!/usr/bin/env python3
"""EduData Mcp Server — MCP Server (upstream image wrapper).

Provides MCP access to EduData Mcp Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("edu-data-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8416"))

mcp = FastMCP("EduData Mcp Server", instructions="Overview edu-data-mcp-server is a Model Context Protocol (MCP) server that provides access to the Urban Institute's Education Data API. It e")


@mcp.tool()
def edu_data_info() -> str:
    """Return basic info / status for EduData Mcp Server."""
    return "EduData Mcp Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting edu-data-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
