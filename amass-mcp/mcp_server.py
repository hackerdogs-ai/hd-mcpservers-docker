#!/usr/bin/env python3
"""Amass MCP Server — subdomain enumeration and reconnaissance. FastMCP, no Minibridge."""
import asyncio
import logging
import os
import shutil
import sys
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("amass-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8382"))
mcp = FastMCP("Amass MCP Server", instructions="Advanced subdomain enumeration and reconnaissance.")
BIN = os.environ.get("AMASS_BIN", "amass")

async def _run(args: list[str], timeout: int = 600) -> dict:
    binary = shutil.which(BIN) or "/usr/local/bin/amass"
    if not os.path.isfile(binary):
        raise FileNotFoundError(f"amass not found at {binary}")
    proc = await asyncio.create_subprocess_exec(binary, *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return {"stdout": "", "stderr": f"Timeout after {timeout}s", "return_code": -1}
    return {"stdout": stdout.decode("utf-8", errors="replace"), "stderr": stderr.decode("utf-8", errors="replace"), "return_code": proc.returncode or 0}

@mcp.tool()
async def run_amass(arguments: str, timeout_seconds: int = 600) -> str:
    """Run amass with the given arguments (e.g. enum -d example.com, or intel -d example.com -whois)."""
    import shlex
    args = shlex.split(arguments) if arguments.strip() else ["-h"]
    logger.info("run_amass arguments=%s", arguments)
    r = await _run(args, timeout=timeout_seconds)
    if r["return_code"] != 0:
        return f"amass failed (exit {r['return_code']}): {(r['stderr'] or r['stdout'] or '').strip()}"
    return (r["stdout"] or "").strip() or "amass completed."

def main():
    logger.info("Starting amass-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)

if __name__ == "__main__":
    main()
