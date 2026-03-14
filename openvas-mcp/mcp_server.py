#!/usr/bin/env python3
"""OpenVAS/GVM MCP Server — Remote client for Greenbone Vulnerability Scanners.

Wraps the gvm-cli to expose capabilities through the Model Context Protocol (MCP).
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
logger = logging.getLogger("openvas-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8300"))

mcp = FastMCP(
    "OpenVAS MCP Server",
    instructions=(
        "API client for interacting with a remote Greenbone Vulnerability Management (OpenVAS) server. "
        "Use this tool to send GMP commands, trigger scans, and retrieve reports via gvm-cli. "
        "IMPORTANT: You must provide valid connection details (e.g., socket, TLS, or SSH) "
        "and credentials to a running OpenVAS infrastructure. "
        "Exported reports will be saved to the configured output directory."
    ),
)

BIN_NAME = os.environ.get("OPENVAS_BIN", "gvm-cli")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the gvm-cli binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed gvm-tools."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a gvm-cli command via the Python interpreter and return structured output."""
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
async def run_openvas(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run gvm-cli with the given arguments.

    Pass arguments as you would on the command line.
    Example: "tls --hostname <target> --gmp-username admin --gmp-password admin <XML_COMMAND>"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_openvas called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("openvas command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"gvm-cli failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"python3 {BIN_NAME} {' '.join(args)}",
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
            "message": "OpenVAS command executed successfully.",
            "stdout": stdout,
        }, indent=2)


def main():
    logger.info("Starting openvas-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()