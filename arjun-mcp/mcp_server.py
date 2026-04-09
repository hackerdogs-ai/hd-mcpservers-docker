#!/usr/bin/env python3
"""Arjun MCP Server — discover hidden HTTP parameters. FastMCP, no Minibridge."""
import asyncio
import logging
import os
import shutil
import sys
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("arjun-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8383"))
mcp = FastMCP("Arjun MCP Server", instructions="Run Arjun to discover hidden HTTP parameters.")
ARJUN_CMD = os.environ.get("ARJUN_CMD", "arjun")

async def _run(cmd: list, timeout: int = 300) -> dict:
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        return {"stdout": "", "stderr": f"Timeout {timeout}s", "return_code": -1}
    return {"stdout": stdout.decode("utf-8", errors="replace"), "stderr": stderr.decode("utf-8", errors="replace"), "return_code": proc.returncode or 0}

@mcp.tool()
async def do_arjun(arguments: str, timeout_seconds: int = 300) -> str:
    """Run Arjun with CLI arguments (e.g. -u https://example.com)."""
    import shlex
    args = shlex.split(arguments) if arguments.strip() else ["-h"]
    cmd = [ARJUN_CMD] + args
    if not shutil.which(ARJUN_CMD) and ARJUN_CMD == "arjun":
        cmd = ["python3", "/opt/arjun/arjun.py"] + args
    logger.info("do_arjun arguments=%s", arguments)
    r = await _run(cmd, timeout=timeout_seconds)
    if r["return_code"] != 0:
        return f"arjun failed (exit {r['return_code']}): {(r['stderr'] or r['stdout'] or '').strip()}"
    return (r["stdout"] or "").strip() or "Done."

def main():
    logger.info("Starting arjun-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)

if __name__ == "__main__":
    main()
