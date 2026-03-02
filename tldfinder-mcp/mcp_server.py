"""TLDFinder MCP Server - TLD & Subdomain Discovery via FastMCP."""

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
logger = logging.getLogger("tldfinder-mcp")

mcp = FastMCP(
    "tldfinder-mcp",
    instructions="MCP server for TLDFinder - discovers private TLDs and subdomains using passive and active DNS.",
)

TLDFINDER_BIN = shutil.which("tldfinder") or "tldfinder"


def _run_tldfinder(args: list[str], timeout: int = 120) -> dict:
    """Execute tldfinder CLI and return structured result."""
    try:
        result = subprocess.run(
            [TLDFINDER_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("tldfinder exited with code %d: %s", result.returncode, stderr)

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

        return {
            "success": result.returncode == 0,
            "output": parsed if parsed is not None else output,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("tldfinder binary not found at '%s'", TLDFINDER_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"tldfinder binary not found at '{TLDFINDER_BIN}'. Ensure tldfinder is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("tldfinder command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"tldfinder command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("tldfinder command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def find_tlds(
    domains: str,
    discovery_mode: str = "",
    sources: str = "",
    exclude_sources: str = "",
    use_all_sources: bool = False,
    active_only: bool = False,
    include_ips: bool = False,
    match_pattern: str = "",
    filter_pattern: str = "",
    timeout: int = 30,
    max_time: int = 10,
) -> dict:
    """Discover TLDs and subdomains for one or more domains using passive and active DNS.

    Args:
        domains: Comma-separated list of target domains.
        discovery_mode: Discovery mode: "dns", "tld", or "domain". Optional.
        sources: Comma-separated list of sources to use. Optional.
        exclude_sources: Comma-separated list of sources to exclude. Optional.
        use_all_sources: Use all available sources. Default False.
        active_only: Use only active DNS discovery. Default False.
        include_ips: Include IP addresses in output. Default False.
        match_pattern: Match pattern to filter results. Optional.
        filter_pattern: Filter pattern to exclude results. Optional.
        timeout: Timeout per domain in seconds. Default 30.
        max_time: Maximum total runtime in minutes. Default 10.

    Returns:
        Dictionary with TLD/subdomain discovery results.
    """
    logger.info("find_tlds called with domains=%s", domains)
    args = ["-json"]

    for domain in domains.split(","):
        domain = domain.strip()
        if domain:
            args.extend(["-d", domain])

    if discovery_mode:
        args.extend(["-dm", discovery_mode])
    if sources:
        args.extend(["-s", sources])
    if exclude_sources:
        args.extend(["-es", exclude_sources])
    if use_all_sources:
        args.append("-all")
    if active_only:
        args.append("-nW")
    if include_ips:
        args.append("-oI")
    if match_pattern:
        args.extend(["-m", match_pattern])
    if filter_pattern:
        args.extend(["-f", filter_pattern])

    args.extend(["-timeout", str(timeout)])
    args.extend(["-max-time", str(max_time)])

    effective_timeout = max(timeout * len(domains.split(",")), max_time * 60) + 30
    return _run_tldfinder(args, timeout=effective_timeout)


@mcp.tool()
def list_sources() -> dict:
    """List all available data sources for TLD and subdomain discovery.

    Returns:
        Dictionary with available source names.
    """
    logger.info("list_sources called")
    return _run_tldfinder(["-ls"])


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8113"))
    logger.info("Starting tldfinder-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
