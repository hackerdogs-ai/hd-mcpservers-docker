#!/usr/bin/env python3
"""Psudohash MCP Server — Password list generator for targeted attacks based on known information.

Wraps the psudohash CLI (t3l3machus/psudohash) to expose
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("psudohash-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8287"))

mcp = FastMCP(
    "Psudohash MCP Server",
    instructions=(
        "Password list generator for targeted attacks based on known information. "
        "Generated wordlists will be saved to the output directory."
    ),
)

# Point directly to the script instead of relying on symlinks or PATH
PSUDOHASH_SCRIPT = os.environ.get("PSUDOHASH_SCRIPT", "/opt/psudohash/psudohash.py")
OUTPUT_DIR = "/app/output"


def _find_script() -> str:
    """Locate the psudohash script directly."""
    if not os.path.exists(PSUDOHASH_SCRIPT):
        logger.error(f"psudohash script not found at {PSUDOHASH_SCRIPT}")
        raise FileNotFoundError(
            f"psudohash script not found at {PSUDOHASH_SCRIPT}. "
            "Ensure the Dockerfile cloned the repository correctly."
        )
    return PSUDOHASH_SCRIPT


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a psudohash command and return structured output."""
    script_path = _find_script()
    
    # Explicitly invoke with sys.executable (Python 3) to bypass shebang/PATH errors
    cmd = [sys.executable, script_path] + args

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # FIX 1: Copy the required padding file into the CWD so psudohash can find it
    padding_src = "/opt/psudohash/common_padding_values.txt"
    padding_dst = os.path.join(OUTPUT_DIR, "common_padding_values.txt")
    if os.path.exists(padding_src) and not os.path.exists(padding_dst):
        try:
            shutil.copy2(padding_src, padding_dst)
        except Exception as e:
            logger.warning("Failed to copy common_padding_values.txt: %s", e)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,  # FIX 2: Open stdin for interactive prompts
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Force all generated wordlists to drop in /app/output!
        )
        
        # FIX 2: Send "y\n" to automatically bypass the interactive combination warning
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=b"y\n"), timeout=timeout_seconds
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
async def run_psudohash(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run psudohash with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string (e.g., "-w admin,1990 -o custom_wordlist.txt").
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_psudohash called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("psudohash command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"psudohash failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"python3 psudohash.py {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # Fallback to STDERR if STDOUT is empty
        if not stdout and stderr:
            stdout = stderr

        if not stdout:
            return json.dumps({"message": "Command completed with no output. Check the output directory.", "arguments": arguments})

        return json.dumps({
            "success": True,
            "message": "Psudohash executed successfully.",
            "stdout": stdout,
            "instructions": "If a wordlist was generated, it is located in the mounted /app/output directory on the host."
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_psudohash: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting psudohash-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()