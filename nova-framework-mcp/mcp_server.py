#!/usr/bin/env python3
"""Nova Framework MCP Server — Automated security testing and prompt pattern matching.

Wraps the novarun CLI (Nova-Hunting/nova-framework) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import sys
import shlex
import shutil

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("nova-framework-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8299"))

mcp = FastMCP(
    "Nova Framework MCP Server",
    instructions=(
        "Automated security testing and prompt pattern matching framework. "
        "Use this to scan prompts for jailbreaks, injections, and TTPs. "
        "IMPORTANT: Official detection rules are available in /opt/nova-rules/ "
        "(e.g., /opt/nova-rules/jailbreak.nov, /opt/nova-rules/injection.nov). "
        "Generated outputs and logs will be saved to the configured output directory."
    ),
)

# Pointing to the actual executable name `novarun`
BIN_NAME = os.environ.get("NOVA_FRAMEWORK_BIN", "novarun")
OUTPUT_DIR = "/app/output"


def _find_binary() -> str:
    """Locate the novarun binary directly."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error(f"{BIN_NAME} binary not found on PATH")
        raise FileNotFoundError(
            f"{BIN_NAME} binary not found. Ensure the Dockerfile built the package correctly."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a novarun command via the Python interpreter and return structured output."""
    binary_path = _find_binary()
    
    # We bypass the OS shebang issues by explicitly executing via Python 3
    cmd = [sys.executable, binary_path] + args

    # Ensure the output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=OUTPUT_DIR  # Route all local output/logs to the mounted volume
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
async def run_nova_framework(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run novarun with the given arguments.

    Pass arguments as you would on the command line.
    Example: "-r /opt/nova-rules/jailbreak.nov -p 'ignore previous instructions'"

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_nova_framework called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("novarun command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"novarun failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"python3 {BIN_NAME} {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Try to parse as JSON, else return standard string
    try:
        parsed = json.loads(stdout)
        return json.dumps(parsed, indent=2)
    except json.JSONDecodeError:
        return json.dumps({
            "success": True,
            "message": "Nova Framework executed successfully.",
            "stdout": stdout,
        }, indent=2)


def main():
    logger.info("Starting nova-framework-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()