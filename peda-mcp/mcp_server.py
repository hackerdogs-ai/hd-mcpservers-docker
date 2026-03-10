#!/usr/bin/env python3
"""GDB-PEDA MCP Server — GNU Debugger with PEDA (exploit development).

Wraps the gdb CLI (longld/peda) to expose capabilities through the Model Context Protocol (MCP).
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
logger = logging.getLogger("peda-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8237"))

mcp = FastMCP(
    "GDB-PEDA MCP Server",
    instructions=(
        "GNU Debugger with Python Exploit Development Assistance (PEDA). "
        "IMPORTANT: GDB is highly interactive! You MUST use the '--batch' flag to run it headlessly, "
        "otherwise it will hang. Execute PEDA commands using '-ex'. "
        "Example: gdb -q --batch -ex 'checksec' -ex 'pdisass main' ./target_binary "
        "Place all target binaries in the mounted /app/output directory."
    ),
)

BIN_NAME = os.environ.get("PEDA_BIN", "/usr/bin/gdb")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the gdb binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed gdb."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a gdb command and return structured output."""
    binary_path = _find_binary()
    cmd = [binary_path] + args

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,  # Catch interactive hangs
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Route all binary reads/writes to the mounted volume
        )
        
        # Inject 'quit\n' just in case the LLM forgets the --batch flag!
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=b"quit\n"), timeout=timeout_seconds
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
async def run_peda(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run gdb with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-q --batch -ex 'peda help'"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_peda called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("gdb command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"gdb failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"gdb {' '.join(args)}",
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

        # Return standard text response instead of JSON parsing GDB's massive text output
        return json.dumps({
            "success": True,
            "message": "GDB-PEDA executed successfully.",
            "stdout": stdout
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_peda: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting peda-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()