#!/usr/bin/env python3
"""Trivy Security MCP server — MCP Server (upstream image wrapper).

Provides MCP access to Trivy Security MCP server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("trivy-security-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8456"))

mcp = FastMCP("Trivy Security MCP server", instructions="A Model Context Protocol (MCP) server that integrates the Trivy security scanner. It enables AI assistants to perform automated security ass")


@mcp.tool()
def trivy_security_info() -> str:
    """Return basic info / status for Trivy Security MCP server."""
    return "Trivy Security MCP server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting trivy-security-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
