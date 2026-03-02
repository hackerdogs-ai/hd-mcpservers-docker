"""Wappalyzergo MCP Server - Web Technology Detection via FastMCP."""

import json
import os
import subprocess
import shutil
import sys
import logging

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("wappalyzergo-mcp")

mcp = FastMCP(
    "wappalyzergo-mcp",
    instructions="MCP server for Wappalyzergo - detect web technologies (frameworks, CMS, servers, libraries) from HTTP headers and HTML content.",
)

WAPPALYZERGO_BIN = shutil.which("wappalyzergo-cli") or "wappalyzergo-cli"


def _run_wappalyzergo(args: list[str], timeout: int = 120) -> dict:
    """Execute wappalyzergo-cli and return structured result."""
    try:
        result = subprocess.run(
            [WAPPALYZERGO_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("wappalyzergo-cli exited with code %d: %s", result.returncode, stderr)

        parsed = None
        if output:
            lines = output.splitlines()
            json_results = []
            for line in lines:
                try:
                    json_results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            if json_results:
                parsed = json_results
            elif not json_results:
                try:
                    parsed = json.loads(output)
                except json.JSONDecodeError:
                    pass

        return {
            "success": result.returncode == 0,
            "output": parsed if parsed is not None else output,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("wappalyzergo-cli binary not found at '%s'", WAPPALYZERGO_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"wappalyzergo-cli binary not found at '{WAPPALYZERGO_BIN}'. Ensure it is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("wappalyzergo-cli command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"wappalyzergo-cli command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("wappalyzergo-cli command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def detect_technologies(
    urls: str,
    timeout: int = 10,
) -> dict:
    """Detect web technologies on target URLs.

    Analyzes one or more URLs to identify web technologies such as frameworks,
    CMS platforms, web servers, JavaScript libraries, analytics tools, and more
    using HTTP headers and HTML content fingerprinting.

    Args:
        urls: Comma-separated URLs to analyze (e.g. "https://example.com,https://google.com").
        timeout: HTTP timeout in seconds for each request. Default 10.

    Returns:
        Dictionary with detected technologies and their categories for each URL.
    """
    logger.info("detect_technologies called with urls=%s", urls)
    url_list = []
    for part in urls.replace(",", "\n").splitlines():
        part = part.strip()
        if part:
            url_list.append(part)

    if not url_list:
        return {"success": False, "output": None, "stderr": "No URLs provided", "exit_code": -1}

    args = ["-urls", ",".join(url_list), "-timeout", str(timeout), "-json"]

    return _run_wappalyzergo(args, timeout=max(120, timeout * len(url_list) + 30))


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8114"))
    logger.info("Starting wappalyzergo-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
