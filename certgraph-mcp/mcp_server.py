#!/usr/bin/env python3
"""CertGraph MCP Server — certificate relationship graphs."""
import asyncio, json, logging, os, shutil, sys
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("certgraph-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8519"))
mcp = FastMCP("CertGraph MCP Server", instructions="Build certificate relationship graphs for domains.")
BIN = os.environ.get("CERTGRAPH_BIN", "certgraph")

@mcp.tool()
async def certgraph_scan(host: str, depth: int = 1, timeout_seconds: int = 180) -> str:
    """Build a certificate graph for a host.
    Args: host: Target hostname. depth: Graph depth. timeout_seconds: Max time."""
    binary = shutil.which(BIN) or "/usr/local/bin/certgraph"
    if not os.path.isfile(binary): return json.dumps({"error": f"certgraph not found at {binary}"})
    args = [binary, "-json", "-depth", str(depth), host]
    try:
        proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        out = stdout.decode("utf-8", errors="replace").strip()
        if proc.returncode != 0:
            return json.dumps({"error": f"certgraph failed (exit {proc.returncode})", "detail": stderr.decode()[:500]})
        try: return json.dumps(json.loads(out), indent=2)
        except: return out or "No output"
    except asyncio.TimeoutError:
        return json.dumps({"error": f"Timeout after {timeout_seconds}s"})

if __name__ == "__main__":
    logger.info("Starting certgraph-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
