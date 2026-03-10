#!/usr/bin/env python3
"""Hashcat MCP Server — GPU-accelerated password recovery.

Wraps the hashcat CLI (hashcat/hashcat) to expose capabilities through the Model Context Protocol (MCP).
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
logger = logging.getLogger("hashcat-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8235"))

mcp = FastMCP(
    "Hashcat MCP Server",
    instructions=(
        "Advanced password recovery and cracking tool. "
        "IMPORTANT: Place target hash files and wordlists in the mounted /app/output directory. "
        "If you are running in a container without a GPU, you may need to append '--force' to your arguments."
    ),
)

BIN_NAME = os.environ.get("HASHCAT_BIN", "/usr/bin/hashcat")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the hashcat binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed hashcat."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a hashcat command and return structured output."""
    binary_path = _find_binary()
    cmd = [binary_path] + args

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Route all hashfile reads and potfile writes to the mounted volume
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
async def run_hashcat(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run hashcat with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-m 0 -a 0 hashes.txt wordlist.txt"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_hashcat called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        # FIX: Hashcat returns 1 if it finished but didn't crack all hashes (Exhausted).
        # We only throw an error if the exit code is not 0 AND not 1.
        if result["return_code"] not in [0, 1]:
            logger.warning("hashcat command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"hashcat failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"hashcat {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # Fallback to STDERR if STDOUT is empty
        if not stdout and stderr:
            stdout = stderr

        if not stdout:
            return json.dumps({"message": "Command completed with no output", "arguments": arguments})

        # Return standard text response
        return json.dumps({
            "success": True,
            "message": "Hashcat executed successfully.",
            "stdout": stdout
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_hashcat: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting hashcat-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()