#!/usr/bin/env python3
"""Grafana MCP Server — MCP Server (upstream image wrapper).

Provides MCP access to Grafana MCP Server via FastMCP with stdio and
streamable-http transports.
"""

import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("acuvity-mcp-server-grafana-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8425"))

mcp = FastMCP("Grafana MCP Server", instructions="The Grafana MCP Server MCP Server provides access to your Grafana instance and the surrounding ecosystem.")


@mcp.tool()
def acuvity_mcp_server_grafana_info() -> str:
    """Return basic info / status for Grafana MCP Server."""
    return "Grafana MCP Server MCP server is running."


if __name__ == "__main__":
    logger.info("Starting acuvity-mcp-server-grafana-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
