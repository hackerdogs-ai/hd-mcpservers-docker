#!/usr/bin/env python3
"""Smuggler MCP Server — HTTP request smuggling detection tool.

Wraps the smuggler CLI (defparam/smuggler) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import sys
import shlex

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("smuggler-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8291"))

mcp = FastMCP(
    "Smuggler MCP Server",
    instructions=(
        "HTTP request smuggling detection tool. "
        "Outputs and logs will be saved to the configured output directory."
    ),
)

# Point directly to the cloned script to avoid PATH/symlink OS errors
SMUGGLER_SCRIPT = os.environ.get("SMUGGLER_SCRIPT", "/opt/smuggler/smuggler.py")
OUTPUT_DIR = "/app/output"


def _find_script() -> str:
    """Locate the smuggler script directly."""
    if not os.path.exists(SMUGGLER_SCRIPT):
        logger.error(f"Smuggler script not found at {SMUGGLER_SCRIPT}")
        raise FileNotFoundError(
            f"Smuggler script not found at {SMUGGLER_SCRIPT}. "
            "Ensure the Dockerfile cloned the repository correctly and you built with --no-cache."
        )
    return SMUGGLER_SCRIPT


def _build_command(args: list[str]) -> list[str]:
    """Build the command list to run smuggler. Use python for .py scripts."""
    binary_path = _find_binary()
    # Resolve symlinks (e.g. /usr/local/bin/smuggler -> /opt/smuggler/smuggler.py)
    if os.path.islink(binary_path):
        target = os.readlink(binary_path)
        link_target = os.path.normpath(os.path.join(os.path.dirname(binary_path), target)) if not os.path.isabs(target) else target
        if os.path.isfile(link_target):
            binary_path = link_target
    if binary_path.endswith(".py") and os.path.isfile(binary_path):
        return [sys.executable, binary_path] + args
    return [binary_path] + args


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a smuggler command via the Python interpreter and return structured output."""
    script_path = _find_script()
    
    # Explicitly invoke with sys.executable (Python 3)
    cmd = [sys.executable, script_path] + args

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
async def run_smuggler(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run smuggler with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string (e.g., "-u https://example.com").
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_smuggler called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("smuggler command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"smuggler failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"python3 smuggler.py {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Return structured JSON for the LLM
    return json.dumps({
        "success": True,
        "message": "Smuggler executed successfully.",
        "stdout": stdout,
    }, indent=2)


def main():
    logger.info("Starting smuggler-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()