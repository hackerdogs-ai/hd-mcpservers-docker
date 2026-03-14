#!/usr/bin/env python3
"""Sublist3r MCP Server — Fast subdomain enumeration tool using OSINT.

Wraps the sublist3r CLI (aboul3la/Sublist3r) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import shlex

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("sublist3r-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8301"))

mcp = FastMCP(
    "Sublist3r MCP Server",
    instructions=(
        "Fast subdomain enumeration tool using OSINT. "
        "IMPORTANT: If you use the '-o' or '--output' flag to save results to a text file, "
        "the file will be saved in the configured output directory."
    ),
)

BIN_NAME = os.environ.get("SUBLIST3R_BIN", "/usr/local/bin/sublist3r")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the sublist3r binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile built the package correctly."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a sublist3r command via the Python interpreter and return structured output."""
    binary_path = _find_binary()
    
    # We explicitly invoke with sys.executable (Python 3) to bypass shebang errors
    cmd = [sys.executable, binary_path] + args

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Route all local output/logs to the mounted volume
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        logger.error("Command timed out after %ds: %s", timeout_seconds, " ".join(cmd))
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds}s: {' '.join(cmd)}",
            "return_code": -1,
        }
    except Exception as exc:
        logger.error("Command execution failed: %s", exc)
        return {
            "stdout": "",
            "stderr": f"Failed to execute command: {exc}",
            "return_code": -1,
        }

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return {
        "stdout": stdout,
        "stderr": stderr,
        "return_code": proc.returncode,
    }


@mcp.tool()
async def run_sublist3r(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run sublist3r with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-d example.com -p 80,443 -o results.txt"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_sublist3r called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("sublist3r command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"sublist3r failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"python3 {BIN_NAME} {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Sublist3r primarily outputs plain text (ASCII art + lines of subdomains)
    return json.dumps({
        "success": True,
        "message": "Sublist3r executed successfully.",
        "stdout": stdout,
        "instructions": "If you used the -o flag, the file is located in the mounted /app/output directory on the host."
    }, indent=2)


def main():
    logger.info("Starting sublist3r-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()