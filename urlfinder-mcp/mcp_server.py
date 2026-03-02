"""URLFinder MCP Server - Passive URL Discovery via FastMCP."""

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
logger = logging.getLogger("urlfinder-mcp")

mcp = FastMCP(
    "urlfinder-mcp",
    instructions="MCP server for URLFinder - passively discovers URLs for domains using Wayback Machine, Common Crawl, and other sources.",
)

URLFINDER_BIN = shutil.which("urlfinder") or "urlfinder"


def _run_urlfinder(args: list[str], stdin_data: str | None = None, timeout: int = 120) -> dict:
    """Execute urlfinder CLI and return structured result."""
    try:
        if stdin_data:
            result = subprocess.run(
                [URLFINDER_BIN] + args,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            result = subprocess.run(
                [URLFINDER_BIN] + args,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("urlfinder exited with code %d: %s", result.returncode, stderr)

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
            elif lines:
                parsed = lines

        return {
            "success": result.returncode == 0,
            "output": parsed if parsed is not None else output,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("urlfinder binary not found at '%s'", URLFINDER_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"urlfinder binary not found at '{URLFINDER_BIN}'. Ensure urlfinder is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("urlfinder command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"urlfinder command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("urlfinder command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def find_urls(
    domains: str,
    sources: str | None = None,
    exclude_sources: str | None = None,
    use_all_sources: bool = False,
    match_pattern: str | None = None,
    filter_pattern: str | None = None,
    timeout: int = 30,
    max_time: int = 10,
) -> dict:
    """Find URLs for target domains using passive sources.

    Passively discovers URLs associated with the given domains by querying
    sources like Wayback Machine, Common Crawl, URLScan, VirusTotal, etc.

    Args:
        domains: Comma-separated list of target domains (e.g. "example.com,google.com").
        sources: Comma-separated list of sources to use (e.g. "waybackarchive,commoncrawl"). Omit for defaults.
        exclude_sources: Comma-separated list of sources to exclude.
        use_all_sources: If True, use all available sources. Default False.
        match_pattern: Regex pattern to match/include in results (e.g. ".*\\.js$").
        filter_pattern: Regex pattern to filter/exclude from results (e.g. ".*\\.png$").
        timeout: Timeout in seconds for each source. Default 30.
        max_time: Maximum total execution time in minutes. Default 10.

    Returns:
        Dictionary with discovered URLs.
    """
    logger.info("find_urls called with domains=%s", domains)
    domain_list = []
    for part in domains.replace(",", "\n").splitlines():
        part = part.strip()
        if part:
            domain_list.append(part)

    if not domain_list:
        return {"success": False, "output": None, "stderr": "No domains provided", "exit_code": -1}

    args = ["-d", ",".join(domain_list), "-jsonl", "-silent"]

    if sources:
        args.extend(["-sources", sources.strip()])

    if exclude_sources:
        args.extend(["-exclude-sources", exclude_sources.strip()])

    if use_all_sources:
        args.append("-all")

    if match_pattern:
        args.extend(["-match", match_pattern.strip()])

    if filter_pattern:
        args.extend(["-filter", filter_pattern.strip()])

    args.extend(["-timeout", str(timeout)])
    args.extend(["-max-time", str(max_time)])

    overall_timeout = (max_time * 60) + 30
    return _run_urlfinder(args, timeout=overall_timeout)


@mcp.tool()
def list_sources() -> dict:
    """List all available URL discovery sources.

    Returns the list of passive sources that urlfinder can query for
    URL discovery (e.g. Wayback Machine, Common Crawl, URLScan, etc.).

    Returns:
        Dictionary with available source names.
    """
    logger.info("list_sources called")
    return _run_urlfinder(["-list-sources", "-silent"])


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8112"))
    logger.info("Starting urlfinder-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
