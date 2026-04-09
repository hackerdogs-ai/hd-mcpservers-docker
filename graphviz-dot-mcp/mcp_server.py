#!/usr/bin/env python3
"""Graphviz DOT MCP Server — render DOT diagrams."""
import base64, json, logging, os, subprocess, sys, tempfile
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("graphviz-dot-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8523"))
mcp = FastMCP("Graphviz DOT MCP Server", instructions="Render Graphviz DOT diagrams to SVG or PNG.")

@mcp.tool()
def render_dot(content: str, output_format: str = "svg") -> str:
    """Render a Graphviz DOT diagram.
    Args: content: DOT source code. output_format: 'svg' or 'png'."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".dot", mode="w", delete=False) as f:
            f.write(content); dot_path = f.name
        out_path = dot_path + "." + output_format
        r = subprocess.run(["dot", f"-T{output_format}", "-o", out_path, dot_path], capture_output=True, text=True, timeout=30)
        os.unlink(dot_path)
        if r.returncode != 0: return json.dumps({"error": r.stderr})
        if output_format == "svg":
            with open(out_path) as f: svg = f.read()
            os.unlink(out_path)
            return json.dumps({"format": "svg", "svg": svg})
        else:
            with open(out_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
            os.unlink(out_path)
            return json.dumps({"format": "png", "base64_length": len(b64)})
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting graphviz-dot-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
