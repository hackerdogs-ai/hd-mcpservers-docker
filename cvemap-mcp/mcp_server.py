#!/usr/bin/env python3
"""Cvemap MCP Server — CVE/vulnerability search and analysis via MCP.

Wraps the cvemap CLI (projectdiscovery/cvemap) to expose CVE searching,
filtering, and analysis capabilities through the Model Context Protocol (MCP).

Cvemap provides a CLI interface for browsing and exploring CVEs, with filtering
by product, vendor, severity, CVSS score, and more.
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
logger = logging.getLogger("cvemap-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8106"))

mcp = FastMCP(
    "Cvemap MCP Server",
    instructions=(
        "CVE and vulnerability search and analysis. Search, filter, and "
        "analyze CVEs by product, vendor, severity, CVSS score, and more."
    ),
)

CVEMAP_BIN = os.environ.get("CVEMAP_BIN", "cvemap")


def _check_api_key() -> str | None:
    """Return a warning message if PDCP_API_KEY is not set."""
    if not os.environ.get("PDCP_API_KEY"):
        return (
            "PDCP_API_KEY not set. Cvemap may be rate-limited without it. "
            "Get a free key at https://cloud.projectdiscovery.io"
        )
    return None


def _find_cvemap() -> str:
    """Locate the cvemap binary, raising a clear error if missing."""
    path = shutil.which(CVEMAP_BIN)
    if path is None:
        logger.error("cvemap binary not found on PATH")
        raise FileNotFoundError(
            f"cvemap binary not found. Ensure it is installed and available "
            f"on PATH, or set CVEMAP_BIN to the full path. "
            f"Install with: go install github.com/projectdiscovery/cvemap/cmd/cvemap@latest"
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 300) -> dict:
    """Execute a cvemap command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    api_warning = _check_api_key()
    if api_warning:
        logger.warning(api_warning)

    cvemap = _find_cvemap()
    cmd = [cvemap] + args

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
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


@mcp.tool()
async def search_cves(
    query: Optional[str] = None,
    product: Optional[str] = None,
    vendor: Optional[str] = None,
    severity: Optional[str] = None,
    cvss_score: Optional[str] = None,
    limit: int = 25,
    detailed: bool = False,
) -> str:
    """Search CVEs with filters.

    Search the CVE database using various filter criteria including product,
    vendor, severity level, and CVSS score thresholds.

    Args:
        query: Free-text search query for CVEs.
        product: Filter by product name (e.g. 'apache http server', 'chrome').
        vendor: Filter by vendor name (e.g. 'microsoft', 'google').
        severity: Filter by severity level — 'low', 'medium', 'high', or 'critical'.
        cvss_score: Filter by CVSS score threshold (e.g. '>=7.0', '9.0').
        limit: Maximum number of results to return (default 25).
        detailed: Include detailed CVE information in results.
    """
    logger.info("search_cves called with query=%s, product=%s, vendor=%s", query, product, vendor)
    args = ["-json"]

    if query:
        args.extend(["-q", query])
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
        logger.warning("cvemap search failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Cvemap search failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"cvemap {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Search completed — no CVEs found matching criteria"})

    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({"raw": line})

    return json.dumps(results, indent=2)


@mcp.tool()
async def get_cve_details(cve_ids: str) -> str:
    """Get details for specific CVE(s).

    Retrieve detailed information for one or more CVE identifiers.

    Args:
        cve_ids: Comma-separated CVE IDs (e.g. 'CVE-2024-1234' or 'CVE-2024-1234,CVE-2024-5678').
    """
    logger.info("get_cve_details called with cve_ids=%s", cve_ids)
    results = []

    for cve_id in cve_ids.split(","):
        cve_id = cve_id.strip()
        if not cve_id:
            continue

        args = ["-id", cve_id, "-json"]
        result = await _run_command(args)

        if result["return_code"] != 0:
            logger.warning("get_cve_details failed for %s with exit code %d", cve_id, result["return_code"])
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
async def list_filters() -> str:
    """List available CVE search filter fields.

    Returns the available filter options and fields that can be used with
    the search_cves tool for refining CVE queries.
    """
    logger.info("list_filters called")
    result = await _run_command(["-help"])

    if result["return_code"] not in (0, 2):
        logger.warning("list_filters failed with exit code %d", result["return_code"])
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
async def analyze_cves(
    field: str,
    query: Optional[str] = None,
) -> str:
    """Aggregate and analyze CVEs by a specific field.

    Provides aggregated statistics for CVEs grouped by the specified field,
    useful for understanding vulnerability trends.

    Args:
        field: Field to aggregate by (e.g. 'severity', 'vendor', 'product', 'year').
        query: Optional search query to narrow the CVE set before aggregation.
    """
    logger.info("analyze_cves called with field=%s, query=%s", field, query)
    args = ["-json"]

    if query:
        args.extend(["-q", query])

    args.extend(["-f", field])

    result = await _run_command(args)

    if result["return_code"] != 0:
        logger.warning("cvemap analysis failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Cvemap analysis failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"cvemap {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Analysis completed — no results"})

    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({"raw": line})

    return json.dumps(results, indent=2)


def main():
    logger.info("Starting cvemap-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
