#!/usr/bin/env python3
"""Radare2 MCP Server — Reverse engineering framework.

Wraps the r2 CLI (radareorg/radare2) to expose capabilities through the Model Context Protocol (MCP).
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
logger = logging.getLogger("radare2-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8239"))

mcp = FastMCP(
    "Radare2 MCP Server",
    instructions=(
        "Reverse engineering framework (radare2/r2). "
        "IMPORTANT: Radare2 is highly interactive by default! You MUST use the '-q' flag "
        "to make it quit after executing commands, otherwise it will hang. "
        "Use '-c' to pass commands. Example: 'r2 -q -c aaa -c afl target_binary'. "
        "Target binaries must be placed in the mounted /app/output directory."
    ),
)

BIN_NAME = os.environ.get("RADARE2_BIN", "/usr/bin/r2")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the r2 binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed radare2."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a r2 command and return structured output."""
    binary_path = _find_binary()
    cmd = [binary_path] + args

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,  # Open stdin to catch interactive hangs
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Route binary reads/writes to the mounted volume
        )
        
        # Send 'q\n' to force quit if it accidentally drops into the interactive prompt!
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=b"q\n"), timeout=timeout_seconds
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
async def run_radare2(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run r2 with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-q -c aaa -c afl /app/output/target_binary"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_radare2 called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("r2 command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"r2 failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"r2 {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # Fallback to STDERR if STDOUT is empty (common for help menus)
        if not stdout and stderr:
            stdout = stderr

        if not stdout:
            return json.dumps({"message": "Command completed with no output. Did you forget the target file?", "arguments": arguments})

        # Radare2 outputs JSON if the LLM uses a `j` command (e.g., -c "ij").
        # We attempt to parse the entire stdout block.
        try:
            parsed = json.loads(stdout)
            return json.dumps(parsed, indent=2)
        except json.JSONDecodeError:
            return json.dumps({
                "success": True,
                "message": "Radare2 executed successfully.",
                "stdout": stdout
            }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_radare2: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting radare2-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()