#!/usr/bin/env python3
"""Generic CLI MCP Server — runs a single CLI binary via MCP.

Uses environment variables:
  CLI_BIN       - binary name (e.g. rustscan)
  MCP_SERVER_TITLE - server name for MCP (e.g. "RustScan MCP Server")
  MCP_SERVER_INSTRUCTIONS - short description for MCP
  MCP_TRANSPORT - stdio or streamable-http
  MCP_PORT      - port for HTTP mode
"""

import asyncio
import logging
import os
import shlex
import shutil
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("cli-mcp")

CLI_BIN = os.environ.get("CLI_BIN", "true")
MCP_SERVER_TITLE = os.environ.get("MCP_SERVER_TITLE", "CLI MCP Server")
MCP_SERVER_INSTRUCTIONS = os.environ.get(
    "MCP_SERVER_INSTRUCTIONS",
    "Run the underlying CLI tool with the given arguments.",
)
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8200"))


mcp = FastMCP(
    MCP_SERVER_TITLE,
    instructions=MCP_SERVER_INSTRUCTIONS,
)


def _find_binary() -> str:
    path = shutil.which(CLI_BIN)
    if path is None:
        raise FileNotFoundError(
            f"CLI binary '{CLI_BIN}' not found on PATH. Set CLI_BIN or install the tool."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    binary = _find_binary()
    cmd = [binary] + args
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds}s",
            "return_code": -1,
        }
    except Exception as e:
        logger.error("Command failed: %s", e)
        return {
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
        }
    return {
        "stdout": stdout_bytes.decode("utf-8", errors="replace"),
        "stderr": stderr_bytes.decode("utf-8", errors="replace"),
        "return_code": proc.returncode or 0,
    }


@mcp.tool()
async def run(arguments: str, timeout_seconds: int = 600) -> str:
    """Run the CLI tool with the given arguments.

    Pass arguments as you would on the command line (e.g. "-a 192.168.1.1 -p 80").
    Use spaces to separate flags and values. For options with values that contain
    spaces, wrap in quotes (e.g. '--option "value with spaces"').

    Args:
        arguments: Command-line arguments string (e.g. "-a 192.168.1.1 -- -sV").
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)
    if result["return_code"] != 0:
        err = result["stderr"] or result["stdout"] or "Unknown error"
        return f"Exit code {result['return_code']}:\n{err}"
    return result["stdout"] or "(no output)"


def main():
    logger.info(
        "Starting %s (transport=%s, port=%s)",
        MCP_SERVER_TITLE,
        MCP_TRANSPORT,
        MCP_PORT,
    )
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
