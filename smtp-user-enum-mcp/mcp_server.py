#!/usr/bin/env python3
"""SMTP User Enum MCP Server — SMTP username enumeration via VRFY, EXPN, and RCPT commands.

Wraps the smtp-user-enum CLI (pentestmonkey/smtp-user-enum) to expose
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
logger = logging.getLogger("smtp-user-enum-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8325"))

mcp = FastMCP(
    "SMTP User Enum MCP Server",
    instructions=(
        "SMTP username enumeration via VRFY, EXPN, and RCPT commands."
    ),
)

BIN_NAME = os.environ.get("SMTP_USER_ENUM_BIN", "smtp-user-enum")


def _find_binary() -> str:
    """Locate the smtp-user-enum binary, raising a clear error if missing."""
    if os.path.isabs(BIN_NAME) and os.path.isfile(BIN_NAME):
        return BIN_NAME
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error("smtp-user-enum binary not found on PATH")
        raise FileNotFoundError(
            f"smtp-user-enum binary not found. Ensure it is installed and available "
            f"on PATH, or set SMTP_USER_ENUM_BIN to the full path."
        )
    return path


def _build_command(args: list[str]) -> list[str]:
    """Build the command list. Run .pl (Perl) scripts with perl interpreter."""
    binary_path = _find_binary()
    # Resolve symlinks to get the real script path
    if os.path.islink(binary_path):
        target = os.readlink(binary_path)
        link_target = os.path.normpath(os.path.join(os.path.dirname(binary_path), target)) if not os.path.isabs(target) else target
        if os.path.isfile(link_target):
            binary_path = link_target
    if binary_path.endswith(".pl") and os.path.isfile(binary_path):
        perl = shutil.which("perl") or "perl"
        return [perl, binary_path] + args
    return [binary_path] + args


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a smtp-user-enum command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    cmd = _build_command(args)

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
async def run_smtp_user_enum(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run smtp-user-enum with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_smtp_user_enum called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("smtp-user-enum command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"smtp-user-enum failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"smtp-user-enum {' '.join(args)}",
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
    logger.info("Starting smtp-user-enum-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
