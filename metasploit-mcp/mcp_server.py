#!/usr/bin/env python3
"""Metasploit MCP Server — Exploitation framework (module runner).

Wraps the msfconsole CLI (rapid7/metasploit-framework) to expose
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
logger = logging.getLogger("metasploit-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8236"))

mcp = FastMCP(
    "Metasploit MCP Server",
    instructions=(
        "Metasploit Framework (msfconsole). "
        "IMPORTANT: msfconsole is interactive and will hang if run normally! "
        "You MUST use the '-q' (quiet) flag and the '-x' flag to execute commands headlessly. "
        "Always append '; exit -y' to your -x commands to ensure the process terminates. "
        "Example: msfconsole -q -x 'use exploit/windows/smb/ms17_010_eternalblue; show options; exit -y'"
    ),
)

BIN_NAME = os.environ.get("METASPLOIT_BIN", "/opt/metasploit-framework/bin/msfconsole")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the msfconsole binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile installed Metasploit."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a msfconsole command and return structured output."""
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
            cwd=OUTPUT_DIR
        )
        
        # Inject 'exit -y\n' just in case the LLM drops into the msf6 > prompt!
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=b"exit -y\n"), timeout=timeout_seconds
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
async def run_metasploit(
    arguments: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run msfconsole with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-q -x 'search eternalblue; exit -y'"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    try:
        if arguments is None:
            arguments = ""
            
        logger.info("run_metasploit called with arguments=%s", arguments)
        args = shlex.split(arguments) if arguments.strip() else []
        
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("msfconsole command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"msfconsole failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"msfconsole {' '.join(args)}",
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

        # Return standard text response instead of JSON parsing the Metasploit console output
        return json.dumps({
            "success": True,
            "message": "Metasploit executed successfully.",
            "stdout": stdout
        }, indent=2)

    except Exception as e:
        logger.error("Unhandled exception in run_metasploit: %s", e)
        return json.dumps({
            "error": True,
            "message": "Internal MCP wrapper error.",
            "detail": str(e)
        }, indent=2)


def main():
    logger.info("Starting metasploit-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()