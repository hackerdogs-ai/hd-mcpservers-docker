#!/usr/bin/env python3
"""NetExec MCP Server — Network service exploitation (formerly CrackMapExec).

Wraps the netexec CLI (PwnDexter/NetExec) to expose
capabilities through the Model Context Protocol (MCP).
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
logger = logging.getLogger("netexec-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8212"))

mcp = FastMCP(
    "NetExec MCP Server",
    instructions=(
        "Network service exploitation (formerly CrackMapExec)."
    ),
)

NETEXEC_BIN = os.environ.get("NETEXEC_BIN", "netexec")


def _find_binary() -> str:
    """Locate the netexec binary, raising a clear error if missing."""
    path = shutil.which(NETEXEC_BIN)
    if path is None:
        logger.error("netexec binary not found on PATH")
        raise FileNotFoundError(
            f"netexec binary not found. Ensure it is installed and available "
            f"on PATH, or set NETEXEC_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a netexec command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
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
async def run_netexec(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run netexec with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_netexec called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("netexec command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"netexec failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"netexec {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Try to parse as JSON/JSONL
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
    logger.info("Starting netexec-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
