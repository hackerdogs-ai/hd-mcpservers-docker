#!/usr/bin/env python3
"""Blackbird MCP Server — Username OSINT search across 500+ sites.

Wraps the blackbird CLI (p1ngul1n0/blackbird) to expose username
search capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shutil
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("blackbird-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8220"))

mcp = FastMCP(
    "Blackbird MCP Server",
    instructions=(
        "Username OSINT tool. Searches for accounts by username "
        "across 500+ websites and social networks. Fast, concurrent "
        "lookups with no API keys required."
    ),
)

BIN_NAME = os.environ.get("BLACKBIRD_BIN", "blackbird")


def _find_binary() -> str:
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error("blackbird binary not found on PATH")
        raise FileNotFoundError(
            f"blackbird binary not found. Ensure it is installed and available "
            f"on PATH, or set BLACKBIRD_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    binary_path = _find_binary()
    cmd = [binary_path] + args

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
async def run_blackbird(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run blackbird with the given arguments.

    Search for a username across 500+ sites.
    Example: "-u johndoe" or "-u johndoe --timeout 30".

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_blackbird called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("blackbird command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"blackbird failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"blackbird {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()
    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({"raw": line})

    if len(results) == 1:
        return json.dumps(results[0], indent=2)
    return json.dumps(results, indent=2)


def main():
    logger.info("Starting blackbird-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
