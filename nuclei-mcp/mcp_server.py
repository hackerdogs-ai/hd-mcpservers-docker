#!/usr/bin/env python3
"""Nuclei MCP Server — run vulnerability templates. FastMCP, no Minibridge."""
import asyncio
import logging
import os
import sys
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("nuclei-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8391"))
mcp = FastMCP("Nuclei MCP Server", instructions="Run nuclei to run vulnerability templates.")
BIN = os.environ.get("BIN", "nuclei")

async def _run(cmd: list, timeout: int = 300) -> dict:
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return {"stdout": "", "stderr": f"Timeout {timeout}s", "return_code": -1}
    return {"stdout": stdout.decode("utf-8", errors="replace"), "stderr": stderr.decode("utf-8", errors="replace"), "return_code": proc.returncode or 0}

def _normalize_nuclei_args(arguments: str) -> list[str]:
    import shlex

    raw = arguments.strip()
    if not raw:
        return ["-h"]
    args = shlex.split(raw)
    # Bare IP/hostname/URL with no flags — treat as scan target.
    if not any(a.startswith("-") for a in args):
        return ["-u", raw]
    return args


def _format_command_output(r: dict) -> str:
    stdout = (r["stdout"] or "").strip()
    stderr = (r["stderr"] or "").strip()
    if stdout and stderr:
        return f"{stdout}\n\n--- stderr ---\n{stderr}"
    if stdout:
        return stdout
    if stderr:
        return stderr
    return "Command completed with no output."


@mcp.tool()
async def run_nuclei(arguments: str, timeout_seconds: int = 300) -> str:
    """Run nuclei with CLI arguments (e.g. -u https://example.com -t cves/)."""
    args = _normalize_nuclei_args(arguments)
    cmd = [BIN] + args
    logger.info("run_nuclei arguments=%s cmd=%s", arguments, cmd)
    r = await _run(cmd, timeout=timeout_seconds)
    if r["return_code"] != 0:
        detail = _format_command_output(r)
        return f"nuclei failed (exit {r['return_code']}):\n{detail}"
    return _format_command_output(r)

def main():
    logger.info("Starting nuclei-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)

if __name__ == "__main__":
    main()
