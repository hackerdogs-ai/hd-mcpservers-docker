#!/usr/bin/env python3
"""AACT Clinical Trials MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to AACT Clinical Trials MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("ctgov-mcp-docker-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8401"))

mcp = FastMCP("AACT Clinical Trials MCP Server", instructions="A Model Context Protocol (MCP) server implementation that provides access to the AACT (Aggregate Analysis of ClinicalTrials.gov https://aact")


@mcp.tool()
def ctgov_mcp_docker_info() -> str:
    """Return basic info / status for AACT Clinical Trials MCP Server."""
    return "AACT Clinical Trials MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting ctgov-mcp-docker-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
