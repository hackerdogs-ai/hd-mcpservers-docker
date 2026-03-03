#!/usr/bin/env python3
"""Evil-WinRM MCP Server — Windows Remote Management shell.

Wraps the evil-winrm CLI (Hackplayers/evil-winrm) to expose
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
logger = logging.getLogger("evil-winrm-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8263"))

mcp = FastMCP(
    "Evil-WinRM MCP Server",
    instructions=(
        "Windows Remote Management shell."
    ),
)

EVIL_WINRM_BIN = os.environ.get("EVIL_WINRM_BIN", "evil-winrm")


def _find_binary() -> str:
    """Locate the evil-winrm binary, raising a clear error if missing."""
    path = shutil.which(EVIL_WINRM_BIN)
    if path is None:
        logger.error("evil-winrm binary not found on PATH")
        raise FileNotFoundError(
            f"evil-winrm binary not found. Ensure it is installed and available "
            f"on PATH, or set EVIL_WINRM_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a evil-winrm command and return structured output.

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
async def run_evil_winrm(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run evil-winrm with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_evil_winrm called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("evil-winrm command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"evil-winrm failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"evil-winrm {' '.join(args)}",
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
    logger.info("Starting evil-winrm-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
