#!/usr/bin/env python3
"""Placeholder MCP for the tools-to-migrate workspace (audit / migration tracking)."""

import json
import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("tools-to-migrate-to-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8512"))

mcp = FastMCP(
    "tools-to-migrate-to-mcp",
    instructions=(
        "Internal workspace for migrating tools to MCP. "
        "See MIGRATION_PLAN.md and repository scripts under this directory."
    ),
)


@mcp.tool()
def workspace_status() -> str:
    """Describe this directory's role in the migration effort."""
    return json.dumps(
        {
            "role": "migration_workspace",
            "documentation": ["MIGRATION_PLAN.md", "PHASE0_VERIFICATION.md"],
            "notes": "Not a production MCP integration; local stub for CI and listing.",
        },
        indent=2,
    )


def main():
    logger.info(
        "Starting tools-to-migrate-to-mcp (transport=%s, port=%s)",
        MCP_TRANSPORT,
        MCP_PORT,
    )
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
