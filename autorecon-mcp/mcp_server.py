#!/usr/bin/env python3
"""AutoRecon MCP Server — Automated reconnaissance. Run AutoRecon with target and options.

Wraps the autorecon CLI (Tib3rius/AutoRecon) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import pty
import shutil
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("autorecon-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8201"))

mcp = FastMCP(
    "AutoRecon MCP Server",
    instructions=(
        "Automated reconnaissance. Run AutoRecon with target and options."
    ),
)

AUTORECON_BIN = os.environ.get("AUTORECON_BIN", "")


def _get_autorecon_cmd_base() -> list[str]:
    """Return argv for autorecon (binary or python -m). Prefer explicit AUTORECON_BIN, then PATH, then python -m."""
    if AUTORECON_BIN:
        path = shutil.which(AUTORECON_BIN) or AUTORECON_BIN
        if path:
            return [path]
    if shutil.which("autorecon"):
        return ["autorecon"]
    # Fallback: run as module (e.g. when installed via pip for python3 and script not on PATH)
    return [sys.executable, "-m", "autorecon"]


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute an autorecon command and return structured output.

    Runs autorecon with a PTY so it sees a TTY (avoids termios error when stdin is not a terminal).
    Returns a dict with keys: stdout, stderr, return_code.
    """
    base = _get_autorecon_cmd_base()
    cmd = base + args
    master_fd = slave_fd = None
    proc = None

    try:
        master_fd, slave_fd = pty.openpty()
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=slave_fd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        if slave_fd is not None:
            os.close(slave_fd)
            slave_fd = None
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
    except asyncio.TimeoutError:
        if proc is not None:
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
        if proc is not None:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
        return {
            "stdout": "",
            "stderr": f"Failed to execute command: {exc}",
            "return_code": -1,
        }
    finally:
        if slave_fd is not None:
            try:
                os.close(slave_fd)
            except OSError:
                pass
        if master_fd is not None:
            try:
                os.close(master_fd)
            except OSError:
                pass

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return {
        "stdout": stdout,
        "stderr": stderr,
        "return_code": proc.returncode,
    }


@mcp.tool()
async def run_autorecon(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run autorecon with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_autorecon called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("autorecon command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"autorecon failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"autorecon {' '.join(args)}",
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
    logger.info("Starting autorecon-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
