#!/usr/bin/env python3
"""MCPScan MCP Server — MCP server security scanning and vulnerability detection.

Wraps the mcpscan CLI (antgroup/MCPScan) to expose
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
logger = logging.getLogger("mcpscan-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8296"))

mcp = FastMCP(
    "MCPScan MCP Server",
    instructions=(
        "MCP server security scanning and vulnerability detection. "
        "Generated reports (like triage_report.json) will be saved to the configured output directory."
    ),
)

MCPSCAN_BIN = os.environ.get("MCPSCAN_BIN", "/usr/local/bin/mcpscan")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the mcpscan script directly."""
    if not os.path.exists(MCPSCAN_BIN):
        logger.error(f"mcpscan binary not found at {MCPSCAN_BIN}")
        raise FileNotFoundError(
            f"mcpscan binary not found at {MCPSCAN_BIN}. "
            "Ensure the Dockerfile built the package correctly."
        )
    return MCPSCAN_BIN


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute an mcpscan command via the Python interpreter and return structured output."""
    binary_path = _find_binary()
    
    # Explicitly invoke with sys.executable (Python 3) to bypass shebang issues
    cmd = [sys.executable, binary_path] + args

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Route all local output/logs (like triage_report.json) to the mounted volume
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
async def run_mcpscan(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run mcpscan with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string (e.g., "scan https://github.com/user/repo").
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_mcpscan called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("mcpscan command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"mcpscan failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"python3 mcpscan {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Return structured JSON for the LLM
    return json.dumps({
        "success": True,
        "message": "MCPScan executed successfully.",
        "stdout": stdout,
        "instructions": "If a report was generated (e.g., triage_report.json), it will be located in the mounted /app/output directory on the host."
    }, indent=2)


def main():
    logger.info("Starting mcpscan-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()