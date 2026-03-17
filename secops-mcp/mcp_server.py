#!/usr/bin/env python3
"""SecOps MCP Server — run security CLI tools (nuclei, subfinder, etc.) via subprocess.

Exposes run_secops_tool(tool_name, args) for whitelisted binaries. Install tools in the image or mount; tools not present return a clear error.
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("secops-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8379"))

mcp = FastMCP(
    "SecOps MCP Server",
    instructions="Run security CLI tools: nuclei, subfinder, naabu, httpx, etc. Use list_tools to see installed tools; run_secops_tool(tool_name, args) to run (args = list of CLI arguments as strings).",
)

ALLOWED_TOOLS = frozenset({
    "nuclei", "subfinder", "naabu", "httpx", "dnsx", "katana", "gau", "waybackurls",
    "ffuf", "gobuster", "nmap", "amass", "sqlmap", "wfuzz", "whatweb", "nikto",
})
DEFAULT_TIMEOUT = 120
MAX_TIMEOUT = 600


def _find_tool(name: str) -> str | None:
    if name not in ALLOWED_TOOLS:
        return None
    return shutil.which(name)


@mcp.tool()
def list_tools() -> str:
    """List which SecOps CLI tools are installed and available on PATH."""
    available = {}
    for name in sorted(ALLOWED_TOOLS):
        path = _find_tool(name)
        available[name] = path if path else None
    return json.dumps({"allowed_tools": list(ALLOWED_TOOLS), "installed": available}, indent=2)


@mcp.tool()
def run_secops_tool(tool_name: str, args: str, timeout_seconds: int = 120) -> str:
    """Run a SecOps CLI tool by name with the given arguments. args: space-separated CLI args (e.g. '-u https://example.com' or '-d example.com'). Only whitelisted tools are allowed."""
    tool_name = (tool_name or "").strip().lower()
    if not tool_name:
        return json.dumps({"error": "tool_name is required"})
    path = _find_tool(tool_name)
    if not path:
        return json.dumps({
            "error": f"Tool '{tool_name}' not found on PATH or not in allow list",
            "allowed": list(ALLOWED_TOOLS),
        })
    timeout = timeout_seconds if isinstance(timeout_seconds, int) else DEFAULT_TIMEOUT
    timeout = max(10, min(timeout, MAX_TIMEOUT))
    arg_list = [a.strip() for a in (args or "").split() if a.strip()]
    try:
        result = subprocess.run(
            [path] + arg_list,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return json.dumps(
            {
                "tool": tool_name,
                "stdout": result.stdout or "",
                "stderr": result.stderr or "",
                "exit_code": result.returncode,
            },
            indent=2,
        )
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Timed out after {timeout}s", "tool": tool_name})
    except Exception as e:
        logger.exception("run_secops_tool failed")
        return json.dumps({"error": str(e), "tool": tool_name})


if __name__ == "__main__":
    logger.info("Starting secops-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
