#!/usr/bin/env python3
"""Vulnx MCP Server — Vulnerability search and analysis via MCP.

Wraps the vulnx CLI (projectdiscovery/cvemap successor) to expose
vulnerability searching, filtering, and analysis capabilities through
the Model Context Protocol (MCP).

Vulnx is the next-generation vulnerability search tool from ProjectDiscovery,
succeeding cvemap with enhanced search capabilities including subcommands
for search, id lookup, filters, and analysis.
"""

import asyncio
import json
import logging
import os
import shutil
import sys
from typing import Optional

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("vulnx-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8116"))

mcp = FastMCP(
    "Vulnx MCP Server",
    instructions=(
        "Vulnerability search and analysis. Search, filter, and analyze "
        "vulnerabilities by product, vendor, severity, CVSS score, and more. "
        "Powered by vulnx — the successor to cvemap from ProjectDiscovery."
    ),
)

VULNX_BIN = os.environ.get("VULNX_BIN", "vulnx")


def _check_api_key() -> str | None:
    """Return a warning message if PDCP_API_KEY is not set."""
    if not os.environ.get("PDCP_API_KEY"):
        return (
            "PDCP_API_KEY not set. Vulnx works without it but is rate-limited "
            "to 10 requests/min. Get a free key at https://cloud.projectdiscovery.io"
        )
    return None


def _find_vulnx() -> str:
    """Locate the vulnx binary, raising a clear error if missing."""
    path = shutil.which(VULNX_BIN)
    if path is None:
        logger.error("vulnx binary not found on PATH")
        raise FileNotFoundError(
            f"vulnx binary not found. Ensure it is installed and available "
            f"on PATH, or set VULNX_BIN to the full path. "
            f"Install with: go install github.com/projectdiscovery/cvemap/cmd/vulnx@latest"
        )
    return path


async def _run_command(args: list[str], stdin_data: str | None = None, timeout_seconds: int = 300) -> dict:
    """Execute a vulnx command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    api_warning = _check_api_key()
    if api_warning:
        logger.warning(api_warning)

    vulnx = _find_vulnx()
    cmd = [vulnx] + args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if stdin_data else asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(input=stdin_data.encode("utf-8") if stdin_data else None),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        logger.error("Command timed out after %ds: %s", timeout_seconds, " ".join(cmd))
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds}s: {' '.join(cmd)}",
            "return_code": -1,
        }
    except Exception as exc:
        logger.error("Command execution failed: %s", exc)
        return {
            "stdout": "",
            "stderr": f"Failed to execute command: {exc}",
            "return_code": -1,
        }

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    return {
        "stdout": stdout,
        "stderr": stderr,
        "return_code": proc.returncode,
    }


def _parse_json_lines(stdout: str) -> list:
    """Parse newline-delimited JSON output into a list of objects."""
    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({"raw": line})
    return results


@mcp.tool()
async def search_vulnerabilities(
    query: Optional[str] = None,
    product: Optional[str] = None,
    vendor: Optional[str] = None,
    severity: Optional[str] = None,
    cvss_score: Optional[str] = None,
    limit: int = 25,
    detailed: bool = False,
) -> str:
    """Search for vulnerabilities with filters.

    Search the vulnerability database using various filter criteria including
    product, vendor, severity level, and CVSS score thresholds.

    Args:
        query: Search query string (e.g. 'apache && severity:high').
        product: Filter by product name (e.g. 'apache http server', 'chrome').
        vendor: Filter by vendor name (e.g. 'microsoft', 'google').
        severity: Filter by severity level — 'low', 'medium', 'high', or 'critical'.
        cvss_score: Filter by CVSS score threshold (e.g. '>=7.0', '9.0').
        limit: Maximum number of results to return (default 25).
        detailed: Include detailed vulnerability information in results.
    """
    logger.info("search_vulnerabilities called with query=%s, product=%s, vendor=%s", query, product, vendor)
    args = ["search", "-json"]

    if query:
        args.append(query)
    if product:
        args.extend(["-p", product])
    if vendor:
        args.extend(["--vendor", vendor])
    if severity:
        args.extend(["--severity", severity])
    if cvss_score:
        args.extend(["--cvss-score", cvss_score])

    args.extend(["--limit", str(limit)])

    if detailed:
        args.append("--detailed")

    result = await _run_command(args)

    if result["return_code"] != 0:
        logger.warning("vulnx search failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Vulnx search failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"vulnx {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Search completed — no vulnerabilities found matching criteria"})

    results = _parse_json_lines(stdout)
    return json.dumps(results, indent=2)


@mcp.tool()
async def get_vulnerability_details(cve_ids: str) -> str:
    """Get details for specific CVE(s).

    Retrieve detailed information for one or more CVE identifiers.
    Accepts CVE IDs via the 'id' subcommand or piped through stdin.

    Args:
        cve_ids: Comma-separated CVE IDs (e.g. 'CVE-2024-1234' or 'CVE-2024-1234,CVE-2024-5678').
    """
    logger.info("get_vulnerability_details called with cve_ids=%s", cve_ids)
    results = []

    for cve_id in cve_ids.split(","):
        cve_id = cve_id.strip()
        if not cve_id:
            continue

        args = ["id", cve_id, "-json"]
        result = await _run_command(args)

        if result["return_code"] != 0:
            logger.warning("get_vulnerability_details failed for %s with exit code %d", cve_id, result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            results.append({
                "cve_id": cve_id,
                "error": True,
                "message": f"Failed to get details (exit code {result['return_code']})",
                "detail": error_detail.strip(),
            })
            continue

        stdout = result["stdout"].strip()
        if not stdout:
            results.append({"cve_id": cve_id, "message": "No details found"})
            continue

        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                results.append({"cve_id": cve_id, "raw": line})

    return json.dumps(results, indent=2)


@mcp.tool()
async def list_search_filters() -> str:
    """List available search filter fields.

    Returns the available filter options and fields that can be used with
    the search_vulnerabilities tool for refining vulnerability queries.
    """
    logger.info("list_search_filters called")
    result = await _run_command(["filters"])

    if result["return_code"] not in (0, 2):
        logger.warning("list_search_filters failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Failed to list filters (exit code {result['return_code']})",
                "detail": error_detail.strip(),
            },
            indent=2,
        )

    output = result["stdout"].strip() or result["stderr"].strip()
    return output if output else json.dumps({"message": "No filter information returned"})


@mcp.tool()
async def analyze_vulnerabilities(
    field: str,
    query: Optional[str] = None,
) -> str:
    """Aggregate vulnerabilities by a specific field.

    Provides aggregated statistics for vulnerabilities grouped by the specified
    field, useful for understanding vulnerability trends and distributions.

    Args:
        field: Field to aggregate by (e.g. 'severity', 'vendor', 'product', 'year').
        query: Optional search query to narrow the vulnerability set before aggregation.
    """
    logger.info("analyze_vulnerabilities called with field=%s, query=%s", field, query)
    args = ["analyze", "-json", "-f", field]

    if query:
        args.append(query)

    result = await _run_command(args)

    if result["return_code"] != 0:
        logger.warning("vulnx analysis failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Vulnx analysis failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"vulnx {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Analysis completed — no results"})

    results = _parse_json_lines(stdout)
    return json.dumps(results, indent=2)


def main():
    logger.info("Starting vulnx-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
