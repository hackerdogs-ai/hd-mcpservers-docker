#!/usr/bin/env python3
"""Binwalk MCP Server — Firmware analysis and extraction.

Wraps the binwalk CLI to expose capabilities through the Model Context Protocol (MCP).
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
logger = logging.getLogger("binwalk-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8241"))

mcp = FastMCP(
    "Binwalk MCP Server",
    instructions=(
        "Firmware analysis and extraction tool. "
        "IMPORTANT: Place target firmware/binaries in the mounted /app/output directory. "
        "If you use the '-e' (extract) flag, the extracted files will automatically "
        "be saved into a new folder within the output directory."
    ),
)

BIN_NAME = os.environ.get("BINWALK_BIN", "/usr/bin/binwalk")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the binwalk binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed the binwalk package."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a binwalk command and return structured output."""
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
            cwd=OUTPUT_DIR  # Route all firmware extraction (-e) to the mounted volume
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
async def run_binwalk(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run binwalk with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-e firmware.bin"

    Args:
        arguments: Command-line arguments string.  Use ``{source}`` as a
                   placeholder for the downloaded file path when using
                   *source_url*.
        source_url: Optional HTTP(S) URL to a firmware image, binary, or
                    archive.  The file is downloaded into the container and
                    its local path replaces any ``{source}`` placeholder in
                    *arguments*, or is appended if no placeholder is present.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_binwalk called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("binwalk command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"binwalk failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"binwalk {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # Fallback to STDERR if STDOUT is empty (common for help menus)
        if not stdout and stderr:
            stdout = stderr

        if not stdout:
            return json.dumps({"message": "Command completed with no output. Did you specify a target file?", "arguments": arguments})

        # Return standard text response instead of attempting to JSON parse ASCII tables
        return json.dumps({
            "success": True,
            "message": "Binwalk executed successfully.",
            "stdout": stdout,
            "instructions": "If you used the extraction flag (-e), check the output directory for the extracted files."
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_binwalk: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting binwalk-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()