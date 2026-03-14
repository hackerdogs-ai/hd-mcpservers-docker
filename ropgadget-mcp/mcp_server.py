#!/usr/bin/env python3
"""ROPgadget MCP Server — ROP/JOP gadget finder.

Wraps the ROPgadget CLI (JonathanSalwan/ROPgadget) to expose
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
import hd_fetch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("ropgadget-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8242"))

mcp = FastMCP(
    "ROPgadget MCP Server",
    instructions=(
        "ROP/JOP gadget finder. "
        "Use this tool to search for Return-Oriented Programming gadgets inside binaries. "
        "IMPORTANT: Place target binaries in the mounted /app/output directory. "
        "Generated outputs and ropchains should also be saved to this directory."
    ),
)

BIN_NAME = os.environ.get("ROPGADGET_BIN", "/usr/local/bin/ROPgadget")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the ROPgadget binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed the ROPgadget package."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a ROPgadget command and return structured output."""
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
            cwd=OUTPUT_DIR  # Route all binary reads/writes to the mounted volume
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
async def run_ropgadget(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run ROPgadget with the given arguments.

    Pass arguments as you would on the command line.
    Example: "--binary ./target_binary --ropchain"

    Args:
        arguments: Command-line arguments string.  Use ``{source}`` as a
                   placeholder for the downloaded file path when using
                   *source_url*.
        source_url: Optional HTTP(S) URL, GitHub/GitLab repo URL, or archive
                    URL.  Downloaded into the container; local path replaces
                    ``{source}`` in *arguments* or is appended.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_ropgadget called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("ROPgadget command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"ROPgadget failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"ROPgadget {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # Fallback to STDERR if STDOUT is empty (common for help menus)
        if not stdout and stderr:
            stdout = stderr

        if not stdout:
            return json.dumps({"message": "Command completed with no output. Did you specify a target --binary?", "arguments": arguments})

        return json.dumps({
            "success": True,
            "message": "ROPgadget executed successfully.",
            "stdout": stdout
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_ropgadget: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting ropgadget-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()