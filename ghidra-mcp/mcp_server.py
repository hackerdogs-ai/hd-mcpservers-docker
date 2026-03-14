#!/usr/bin/env python3
"""Ghidra MCP Server — NSA reverse engineering suite (headless).

Wraps the analyzeHeadless CLI (NationalSecurityAgency/ghidra) to expose
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
logger = logging.getLogger("ghidra-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8240"))

mcp = FastMCP(
    "Ghidra MCP Server",
    instructions=(
        "NSA reverse engineering suite (headless). "
        "IMPORTANT: analyzeHeadless requires a project directory and a project name as the first two arguments. "
        "Always use /app/output as the project directory! "
        "Example: /app/output MyProject -import target_binary.exe -postScript my_script.py"
    ),
)

BIN_NAME = os.environ.get("GHIDRA_BIN", "/usr/local/bin/analyzeHeadless")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the analyzeHeadless bash script directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed Ghidra and Java correctly."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 1800) -> dict:
    """Execute analyzeHeadless and return structured output. Note: Ghidra takes a long time!"""
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
            cwd=OUTPUT_DIR  # Route all Ghidra project files (.rep) to the mounted volume
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
async def run_ghidra(
    arguments: str = "",
    timeout_seconds: int = 1800, # Increased default timeout to 30 mins because Ghidra is slow
) -> str:
    """Run analyzeHeadless with the given arguments.

    Pass arguments as you would on the command line.
    Example: "/app/output TempProject -import my_malware.bin"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 1800s / 30m).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_ghidra called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("analyzeHeadless command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"analyzeHeadless failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"analyzeHeadless {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # Fallback to STDERR if STDOUT is empty (common for help menus)
        if not stdout and stderr:
            stdout = stderr

        if not stdout:
            return json.dumps({"message": "Command completed with no output. Note: Ghidra requires a project path and name.", "arguments": arguments})

        # Return standard text response instead of attempting to JSON parse Ghidra's massive logs
        return json.dumps({
            "success": True,
            "message": "Ghidra analysis executed successfully.",
            "stdout": stdout,
            "instructions": "Ghidra project files (.gpr and .rep) are located in the mounted /app/output directory."
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_ghidra: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting ghidra-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()