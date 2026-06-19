#!/usr/bin/env python3
"""Local compliance stub for GitHub MCP (Copilot API). Production uses the hosted URL in mcpServer.json."""

import json
import logging
import os
import sys

from fastmcp import FastMCP

REMOTE_URL = "https://api.githubcopilot.com/mcp/"
SERVER_KEY = "github"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(SERVER_KEY)

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8521"))

mcp = FastMCP(
    SERVER_KEY,
    instructions=(
        "GitHub MCP (streamable HTTP on api.githubcopilot.com). Use the hosted endpoint "
        f"{REMOTE_URL} with your GitHub token for full tools. "
        "This image is a minimal local stub for CI (stdio + streamable HTTP)."
    ),
)


@mcp.tool()
def remote_endpoint_info() -> str:
    """Return the official remote MCP URL and notes for this integration."""
    return json.dumps(
        {
            "remote_mcp_url": REMOTE_URL,
            "notes": "Configure Authorization in your client for production.",
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
