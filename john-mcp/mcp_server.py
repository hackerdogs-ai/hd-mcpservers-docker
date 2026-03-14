#!/usr/bin/env python3
"""John the Ripper MCP Server — Password hash cracking with custom rules.

Wraps the john CLI (openwall/john) to expose capabilities through the Model Context Protocol (MCP).
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
logger = logging.getLogger("john-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8234"))

mcp = FastMCP(
    "John the Ripper MCP Server",
    instructions=(
        "CPU-based password cracking tool (John the Ripper). "
        "IMPORTANT: Place target hash files and wordlists in the mounted /app/output directory. "
        "Use '--show' to display previously cracked passwords from the potfile."
    ),
)

BIN_NAME = os.environ.get("JOHN_BIN", "/opt/john/run/john")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the john binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed john."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a john command and return structured output."""
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
            cwd=OUTPUT_DIR  # Route all hash reads to the mounted volume
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
async def run_john(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run john with the given arguments.

    Pass arguments as you would on the command line.
    Example: "--wordlist=words.txt hashes.txt" or "--show hashes.txt"

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
            
        logger.info("run_john called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        # FIX: JtR often returns 1 if it finishes without cracking all hashes.
        if result["return_code"] not in [0, 1]:
            logger.warning("john command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"john failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"john {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # FIX: John outputs "Loaded X password hashes" to STDERR, and cracked passwords to STDOUT.
        # We must combine them so the LLM gets the full context.
        combined_output = stdout
        if stderr:
            combined_output = f"{stderr}\n{stdout}".strip()

        if not combined_output:
            return json.dumps({"message": "Command completed with no output. Did you provide a valid hash file?", "arguments": arguments})

        # Return standard text response instead of JSON parsing
        return json.dumps({
            "success": True,
            "message": "John the Ripper executed successfully.",
            "stdout": combined_output
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_john: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting john-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()