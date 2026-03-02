"""OpenRisk MCP Server - Nuclei Scan Risk Scoring via FastMCP."""

import os
import subprocess
import shutil
import tempfile
import sys
import logging

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("openrisk-mcp")

mcp = FastMCP(
    "openrisk-mcp",
    instructions="MCP server for OpenRisk - generates risk scores from Nuclei scan output using OpenAI GPT-4o.",
)

OPENRISK_BIN = shutil.which("openrisk") or "openrisk"


def _run_openrisk(args: list[str], timeout: int = 300) -> dict:
    """Execute openrisk CLI and return structured result."""
    try:
        result = subprocess.run(
            [OPENRISK_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("openrisk exited with code %d: %s", result.returncode, stderr)

        return {
            "success": result.returncode == 0,
            "output": output if output else None,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("openrisk binary not found at '%s'", OPENRISK_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"openrisk binary not found at '{OPENRISK_BIN}'. Ensure openrisk is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("openrisk command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"openrisk command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("openrisk command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def analyze_risk(
    scan_results: str,
) -> dict:
    """Analyze Nuclei scan results and generate a risk score using OpenAI GPT-4o.

    Writes the provided scan results to a temporary file and runs openrisk
    against it to produce a risk assessment.

    Requires the OPENAI_API_KEY environment variable to be set.

    Args:
        scan_results: Content of Nuclei scan results (text, markdown, or JSONL format).

    Returns:
        Dictionary with risk analysis output including risk score and recommendations.
    """
    logger.info("analyze_risk called")
    if not os.environ.get("OPENAI_API_KEY"):
        return {
            "success": False,
            "output": None,
            "stderr": "OPENAI_API_KEY environment variable is not set. OpenRisk requires an OpenAI API key.",
            "exit_code": -1,
        }

    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, dir="/tmp"
        ) as tmp:
            tmp.write(scan_results)
            tmp_path = tmp.name

        result = _run_openrisk(["-f", tmp_path])
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8115"))
    logger.info("Starting openrisk-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
