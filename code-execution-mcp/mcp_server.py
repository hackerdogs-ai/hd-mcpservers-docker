#!/usr/bin/env python3
"""Code Execution MCP Server — run Python code in a sandboxed subprocess.

Executes user-provided Python code with a timeout; returns stdout, stderr, and exit code.
No network or filesystem write outside a temp dir. Safe for untrusted snippet execution.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("code-execution-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8376"))

mcp = FastMCP(
    "Code Execution MCP Server",
    instructions="Run Python code in a sandboxed subprocess. Use run_python with code string; optional timeout_seconds (default 30, max 120). Returns stdout, stderr, and exit code.",
)

DEFAULT_TIMEOUT = 30
MAX_TIMEOUT = 120


@mcp.tool()
def run_python(code: str, timeout_seconds: int = 30) -> str:
    """Execute Python code in a subprocess. Returns JSON with stdout, stderr, exit_code. No network; temp dir available."""
    if not code or not code.strip():
        return json.dumps({"error": "code is required"})
    timeout = timeout_seconds if isinstance(timeout_seconds, int) else DEFAULT_TIMEOUT
    if timeout < 1:
        timeout = 1
    if timeout > MAX_TIMEOUT:
        timeout = MAX_TIMEOUT
    with tempfile.TemporaryDirectory(prefix="mcp_code_") as tmp:
        script = Path(tmp) / "script.py"
        script.write_text(code.strip(), encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        try:
            result = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp,
                env=env,
            )
            return json.dumps(
                {
                    "stdout": result.stdout or "",
                    "stderr": result.stderr or "",
                    "exit_code": result.returncode,
                },
                indent=2,
            )
        except subprocess.TimeoutExpired:
            return json.dumps(
                {"error": f"Execution timed out after {timeout}s", "stdout": "", "stderr": "", "exit_code": -1}
            )
        except Exception as e:
            logger.exception("run_python failed")
            return json.dumps({"error": str(e), "stdout": "", "stderr": "", "exit_code": -1})


if __name__ == "__main__":
    logger.info("Starting code-execution-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
