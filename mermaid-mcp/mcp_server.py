#!/usr/bin/env python3
"""Mermaid MCP Server — render Mermaid diagrams."""
import base64, json, logging, os, subprocess, sys, tempfile
from fastmcp import FastMCP
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("mermaid-mcp")
MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8524"))
mcp = FastMCP("Mermaid MCP Server", instructions="Render Mermaid diagrams to SVG or PNG.")

@mcp.tool()
def render_mermaid(content: str, output_format: str = "svg") -> str:
    """Render a Mermaid diagram.
    Args: content: Mermaid source code. output_format: 'svg' or 'png'."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".mmd", mode="w", delete=False) as f:
            f.write(content); mmd_path = f.name
        out_path = mmd_path + "." + output_format
        r = subprocess.run(["mmdc", "-i", mmd_path, "-o", out_path, "-b", "transparent"], capture_output=True, text=True, timeout=60)
        os.unlink(mmd_path)
        if r.returncode != 0: return json.dumps({"error": r.stderr or "mmdc failed"})
        if output_format == "svg":
            with open(out_path) as f: svg = f.read()
            os.unlink(out_path)
            return json.dumps({"format": "svg", "svg": svg})
        else:
            with open(out_path, "rb") as f: b64 = base64.b64encode(f.read()).decode()
            os.unlink(out_path)
            return json.dumps({"format": "png", "base64_length": len(b64)})
    except FileNotFoundError:
        return json.dumps({"error": "mmdc (mermaid-cli) not found. Install: npm install -g @mermaid-js/mermaid-cli"})
    except Exception as e:
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    logger.info("Starting mermaid-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio": mcp.run(transport="stdio", show_banner=False)
    else: mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
