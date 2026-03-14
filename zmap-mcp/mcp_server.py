#!/usr/bin/env python3
"""ZMap MCP Server — High-speed single-packet network scanner for internet-wide surveys.

Wraps the zmap CLI (zmap/zmap) to expose
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
logger = logging.getLogger("zmap-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8303"))

mcp = FastMCP(
    "ZMap MCP Server",
    instructions=(
        "High-speed single-packet network scanner for internet-wide surveys. "
        "IMPORTANT: When generating output using the '-o' flag, the file will be "
        "saved directly to the configured output directory."
    ),
)

BIN_NAME = os.environ.get("ZMAP_BIN", "/usr/sbin/zmap")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the zmap binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile built the package correctly."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a zmap command and return structured output."""
    binary_path = _find_binary()
    cmd = [binary_path] + args

    # Ensure output directory exists so generated reports aren't lost
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Route all local output/logs (-o) to the mounted volume
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
async def run_zmap(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run zmap with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-p 80 192.168.1.0/24 -o results.csv"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_zmap called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("zmap command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"zmap failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"zmap {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Try to parse as JSON, else return standard string
    try:
        parsed = json.loads(stdout)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return json.dumps({
            "success": True,
            "message": "ZMap executed successfully.",
            "stdout": stdout,
            "instructions": "If you used the -o flag, the file is located in the mounted /app/output directory on the host."
        }, indent=2)


def main():
    logger.info("Starting zmap-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()