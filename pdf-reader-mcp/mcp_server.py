#!/usr/bin/env python3
"""PDF Reader MCP Server (Sylphx) — MCP Server (upstream image wrapper).

Provides MCP access to PDF Reader MCP Server (Sylphx) via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("pdf-reader-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8442"))

mcp = FastMCP("PDF Reader MCP Server (Sylphx)", instructions="MCP server for reading and extracting text from PDF files via URLs. Uses @sylphx/pdf-reader-mcp npm package. Supports PDF URLs via sources a")


@mcp.tool()
def pdf_reader_info() -> str:
    """Return basic info / status for PDF Reader MCP Server (Sylphx)."""
    return "PDF Reader MCP Server (Sylphx) MCP server is running."


if __name__ == "__main__":
    logger.info("Starting pdf-reader-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
