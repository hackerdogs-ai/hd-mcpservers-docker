"""Asnmap MCP Server - ASN to Network Range Mapping via FastMCP."""

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
logger = logging.getLogger("asnmap-mcp")

mcp = FastMCP(
    "asnmap-mcp",
    instructions="MCP server for Asnmap - maps organization network ranges from ASN, IP, domain, and organization lookups.",
)

ASNMAP_BIN = shutil.which("asnmap") or "asnmap"


def _check_api_key() -> str | None:
    """Check for PDCP_API_KEY and return a warning message if missing."""
    if not os.environ.get("PDCP_API_KEY"):
        return (
            "PDCP_API_KEY environment variable is not set. "
            "Asnmap requires a ProjectDiscovery Cloud Platform API key. "
            "Get one free at https://cloud.projectdiscovery.io/?ref=api_key"
        )
    return None


def _run_asnmap(args: list[str], timeout: int = 60) -> dict:
    """Execute asnmap CLI and return structured result."""
    api_warning = _check_api_key()
    if api_warning:
        logger.warning(api_warning)

    try:
        result = subprocess.run(
            [ASNMAP_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("asnmap exited with code %d: %s", result.returncode, stderr)

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
        logger.error("asnmap binary not found at '%s'", ASNMAP_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"asnmap binary not found at '{ASNMAP_BIN}'. Ensure asnmap is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("asnmap command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"asnmap command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("asnmap command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def lookup_asn(asn: str) -> dict:
    """Look up network ranges associated with an ASN number.

    Maps an Autonomous System Number to its advertised IP ranges,
    providing visibility into an organization's network infrastructure.

    Args:
        asn: ASN number to look up (e.g. "AS5650" or "5650").

    Returns:
        Dictionary with network ranges and ASN information.
    """
    logger.info("lookup_asn called with asn=%s", asn)
    args = ["-json", "-a", asn]
    return _run_asnmap(args)


@mcp.tool()
def lookup_ip(ip: str) -> dict:
    """Look up ASN and network information for an IP address.

    Resolves an IP address to its parent ASN, organization, and
    associated network range.

    Args:
        ip: IP address to look up (e.g. "100.19.12.21").

    Returns:
        Dictionary with ASN information for the IP.
    """
    logger.info("lookup_ip called with ip=%s", ip)
    args = ["-json", "-i", ip]
    return _run_asnmap(args)


@mcp.tool()
def lookup_domain(domain: str) -> dict:
    """Look up ASN and network information for a domain.

    Resolves a domain name to its hosting ASN, organization, and
    associated network ranges.

    Args:
        domain: Domain name to look up (e.g. "example.com").

    Returns:
        Dictionary with ASN information for the domain.
    """
    logger.info("lookup_domain called with domain=%s", domain)
    args = ["-json", "-d", domain]
    return _run_asnmap(args)


@mcp.tool()
def lookup_org(org: str) -> dict:
    """Look up ASN and network information for an organization.

    Searches for ASN records matching the organization name and returns
    associated network ranges.

    Args:
        org: Organization name to look up (e.g. "Google").

    Returns:
        Dictionary with ASN information for the organization.
    """
    logger.info("lookup_org called with org=%s", org)
    args = ["-json", "-org", org]
    return _run_asnmap(args)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8110"))
    logger.info("Starting asnmap-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
