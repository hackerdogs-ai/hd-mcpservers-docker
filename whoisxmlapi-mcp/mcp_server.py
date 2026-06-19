#!/usr/bin/env python3
"""Local compliance stub for WhoisXML API. Production: https://mcp.whoisxmlapi.com/mcp"""

import json
import logging
import os
import sys

from fastmcp import FastMCP

REMOTE_URL = "https://mcp.whoisxmlapi.com/mcp"
SERVER_KEY = "whoisxmlapi"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(SERVER_KEY)

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8511"))

mcp = FastMCP(
    SERVER_KEY,
    instructions=(
        "WhoisXML API MCP. Use the hosted endpoint "
        f"{REMOTE_URL} for full tools. This image is a minimal local stub for CI."
    ),
)


@mcp.tool()
def remote_endpoint_info() -> str:
    """Return the official remote MCP URL and notes for this integration."""
    return json.dumps(
        {
            "remote_mcp_url": REMOTE_URL,
            "notes": "Use the remote URL in your MCP client for production tools.",
        },
        indent=2,
    )


def main():
    logger.info("Starting %s (transport=%s, port=%s)", SERVER_KEY, MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
