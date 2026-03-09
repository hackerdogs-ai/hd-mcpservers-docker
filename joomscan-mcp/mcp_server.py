#!/usr/bin/env python3
"""JoomScan MCP Server — OWASP Joomla vulnerability scanner.

Wraps the joomscan CLI (OWASP/joomscan) to expose
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
logger = logging.getLogger("joomscan-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8305"))

mcp = FastMCP(
    "JoomScan MCP Server",
    instructions=(
        "OWASP Joomla vulnerability scanner. "
        "Use this to enumerate Joomla versions, components, and misconfigurations. "
        "IMPORTANT: Generated HTML and text reports are automatically saved to "
        "the configured output directory on the host."
    ),
)

BIN_NAME = os.environ.get("JOOMSCAN_BIN", "/opt/joomscan/joomscan.pl")
EXEC_DIR = "/opt/joomscan"


def _find_binary() -> str:
    """Locate the joomscan script directly."""
    if not os.path.exists(BIN_NAME):
        logger.error(f"joomscan script not found at {BIN_NAME}")
        raise FileNotFoundError(
            f"joomscan script not found at {BIN_NAME}. "
            "Ensure the Dockerfile cloned the repository correctly."
        )
    return BIN_NAME


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a joomscan command and return structured output."""
    binary_path = _find_binary()
    
    # We explicitly invoke via the Perl interpreter to bypass CRLF shebang issues!
    cmd = ["perl", binary_path] + args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=EXEC_DIR  # Must run from its own directory to find internal databases
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
async def run_joomscan(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run joomscan with the given arguments.

    Pass arguments as you would on the command line.
    Example: "--url http://example.com --enumerate-components"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_joomscan called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("joomscan command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"joomscan failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"perl joomscan.pl {' '.join(args)}",
                },
                indent=2,
            )

        stdout = result["stdout"].strip()
        stderr = result["stderr"].strip()

        # FIX: If the tool returns 0 but prints its help menu/output entirely to STDERR, fallback to it!
        if not stdout and stderr:
            stdout = stderr

        if not stdout:
            return json.dumps({"message": "Command completed with no output", "arguments": arguments})

        return json.dumps({
            "success": True,
            "message": "JoomScan executed successfully.",
            "stdout": stdout,
            "instructions": "If a report was generated, it is located in the mounted /app/output directory on the host."
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_joomscan: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting joomscan-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()