#!/usr/bin/env python3
"""Nova Proximity MCP Server — Network proximity analysis and threat detection.

Wraps the novaprox.py CLI (Nova-Hunting/nova-proximity) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import sys
import shlex

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("nova-proximity-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8298"))

mcp = FastMCP(
    "Nova Proximity MCP Server",
    instructions=(
        "Network proximity analysis and threat detection. "
        "IMPORTANT: When generating reports using --json-report or --md-report, "
        "you MUST explicitly provide the path as /app/output/filename.json to save them to the host volume."
    ),
)

# Correct script name
NOVA_PROXIMITY_SCRIPT = os.environ.get("NOVA_PROXIMITY_SCRIPT", "/opt/nova-proximity/novaprox.py")


def _find_script() -> str:
    """Locate the novaprox script directly."""
    if not os.path.exists(NOVA_PROXIMITY_SCRIPT):
        logger.error(f"nova-proximity script not found at {NOVA_PROXIMITY_SCRIPT}")
        raise FileNotFoundError(
            f"nova-proximity script not found at {NOVA_PROXIMITY_SCRIPT}. "
            "Ensure the Dockerfile cloned the repository correctly and you built with --no-cache."
        )
    return NOVA_PROXIMITY_SCRIPT


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a novaprox command via the Python interpreter and return structured output."""
    script_path = _find_script()
    
    # Explicitly invoke with sys.executable (Python 3) to bypass shebang errors
    cmd = [sys.executable, script_path] + args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/opt/nova-proximity"  # Must run here to find default .nov rule files
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
async def run_nova_proximity(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run nova-proximity with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string (e.g., "-n -r my_rule.nov --json-report /app/output/report.json").
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_nova_proximity called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("nova-proximity command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"nova-proximity failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"python3 novaprox.py {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    # Return structured JSON for the LLM
    return json.dumps({
        "success": True,
        "message": "Nova Proximity executed successfully.",
        "stdout": stdout,
    }, indent=2)


def main():
    logger.info("Starting nova-proximity-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()