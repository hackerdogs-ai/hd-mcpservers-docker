#!/usr/bin/env python3
"""dnsReaper MCP Server — Subdomain takeover vulnerability scanner via DNS.

Wraps the dnsReaper CLI (punk-security/dnsReaper) to expose
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
logger = logging.getLogger("dnsreaper-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8293"))

mcp = FastMCP(
    "dnsReaper MCP Server",
    instructions=(
        "Subdomain takeover vulnerability scanner via DNS. "
        "Generated reports (like results.csv) will be saved to the configured output directory."
    ),
)

# Point directly to the cloned script (main.py)
DNSREAPER_SCRIPT = os.environ.get("DNSREAPER_SCRIPT", "/opt/dnsreaper/main.py")
OUTPUT_DIR = "/app/output"


def _find_script() -> str:
    """Locate the dnsReaper script directly."""
    if not os.path.exists(DNSREAPER_SCRIPT):
        logger.error(f"dnsReaper script not found at {DNSREAPER_SCRIPT}")
        raise FileNotFoundError(
            f"dnsReaper script not found at {DNSREAPER_SCRIPT}. "
            "Ensure the Dockerfile cloned the repository correctly and you built with --no-cache."
        )
    return DNSREAPER_SCRIPT


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a dnsReaper command via the Python interpreter and return structured output."""
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
            cwd=OUTPUT_DIR  # Route all local output/logs (like results.csv) to the mounted volume
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
async def run_dnsreaper(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run dnsReaper with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string (e.g., "single --domain example.com").
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_dnsreaper called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("dnsReaper command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"dnsReaper failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"python3 main.py {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Return structured JSON for the LLM
    return json.dumps({
        "success": True,
        "message": "dnsReaper executed successfully.",
        "stdout": stdout,
        "instructions": "If a report was generated (e.g., results.csv), it will be located in the mounted /app/output directory on the host."
    }, indent=2)


def main():
    logger.info("Starting dnsreaper-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()