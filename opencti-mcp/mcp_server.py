#!/usr/bin/env python3
"""OpenCTI MCP Server — Threat intelligence platform queries via pycti.

Uses the pycti Python client to query OpenCTI platforms,
exposing capabilities through the Model Context Protocol (MCP).
"""

import json
import logging
import os
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("opencti-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8370"))

mcp = FastMCP(
    "OpenCTI MCP Server",
    instructions=(
        "Threat intelligence platform queries via the OpenCTI API. "
        "Search indicators (IOCs), malware, threat actors, reports, "
        "and MITRE ATT&CK techniques. Requires OPENCTI_API_KEY and OPENCTI_URL."
    ),
)


def _get_client():
    """Create and return an OpenCTI API client.

    Returns (client, None) on success or (None, error_json_str) on failure.
    """
    url = os.environ.get("OPENCTI_URL", "").strip()
    api_key = os.environ.get("OPENCTI_API_KEY", "").strip()

    if not url or not api_key:
        missing = []
        if not url:
            missing.append("OPENCTI_URL")
        if not api_key:
            missing.append("OPENCTI_API_KEY")
        err = json.dumps({
            "error": True,
            "message": f"Missing required environment variable(s): {', '.join(missing)}",
            "detail": "Set OPENCTI_URL and OPENCTI_API_KEY to connect to your OpenCTI instance.",
        }, indent=2)
        return None, err

    try:
        from pycti import OpenCTIApiClient
    except ImportError as exc:
        err = json.dumps({
            "error": True,
            "message": "pycti library not available",
            "detail": str(exc),
        }, indent=2)
        return None, err

    try:
        client = OpenCTIApiClient(url, api_key)
        return client, None
    except Exception as exc:
        err = json.dumps({
            "error": True,
            "message": "Failed to create OpenCTI API client",
            "detail": str(exc),
        }, indent=2)
        return None, err


@mcp.tool()
async def opencti_search_indicators(
    query: str,
    limit: int = 10,
) -> str:
    """Search for indicators of compromise (IOCs) in OpenCTI.

    Returns matching indicators such as IP addresses, domains, hashes, URLs, etc.

    Args:
        query: Search query string (e.g. an IP, domain, hash, or keyword).
        limit: Maximum number of results to return (default 10).
    """
    logger.info("opencti_search_indicators query=%s limit=%d", query, limit)

    client, err = _get_client()
    if err:
        return err

    try:
        indicators = client.indicator.list(
            search=query,
            first=limit,
        )
        return json.dumps({
            "tool": "opencti_search_indicators",
            "query": query,
            "count": len(indicators),
            "results": indicators,
        }, indent=2, default=str)
    except Exception as exc:
        logger.error("opencti_search_indicators failed: %s", exc)
        return json.dumps({
            "error": True,
            "message": "Failed to search indicators",
            "detail": str(exc),
        }, indent=2, default=str)


@mcp.tool()
async def opencti_search_malware(
    query: str,
    limit: int = 10,
) -> str:
    """Search for malware entries in OpenCTI.

    Returns matching malware families, strains, and related intelligence.

    Args:
        query: Search query string (e.g. malware name or keyword).
        limit: Maximum number of results to return (default 10).
    """
    logger.info("opencti_search_malware query=%s limit=%d", query, limit)

    client, err = _get_client()
    if err:
        return err

    try:
        malware = client.malware.list(
            search=query,
            first=limit,
        )
        return json.dumps({
            "tool": "opencti_search_malware",
            "query": query,
            "count": len(malware),
            "results": malware,
        }, indent=2, default=str)
    except Exception as exc:
        logger.error("opencti_search_malware failed: %s", exc)
        return json.dumps({
            "error": True,
            "message": "Failed to search malware",
            "detail": str(exc),
        }, indent=2, default=str)


@mcp.tool()
async def opencti_search_threat_actors(
    query: str,
    limit: int = 10,
) -> str:
    """Search for threat actors (groups) in OpenCTI.

    Returns matching threat actor profiles and related intelligence.

    Args:
        query: Search query string (e.g. threat actor name or keyword).
        limit: Maximum number of results to return (default 10).
    """
    logger.info("opencti_search_threat_actors query=%s limit=%d", query, limit)

    client, err = _get_client()
    if err:
        return err

    try:
        threat_actors = client.threat_actor_group.list(
            search=query,
            first=limit,
        )
        return json.dumps({
            "tool": "opencti_search_threat_actors",
            "query": query,
            "count": len(threat_actors),
            "results": threat_actors,
        }, indent=2, default=str)
    except Exception as exc:
        logger.error("opencti_search_threat_actors failed: %s", exc)
        return json.dumps({
            "error": True,
            "message": "Failed to search threat actors",
            "detail": str(exc),
        }, indent=2, default=str)


@mcp.tool()
async def opencti_get_report(
    report_id: str = "",
    query: str = "",
    limit: int = 10,
) -> str:
    """Get a specific report by ID or search reports in OpenCTI.

    Provide report_id to fetch a single report, or query to search.

    Args:
        report_id: OpenCTI report ID to fetch directly (optional).
        query: Search query string for reports (optional).
        limit: Maximum number of results when searching (default 10).
    """
    logger.info("opencti_get_report report_id=%s query=%s limit=%d", report_id, query, limit)

    client, err = _get_client()
    if err:
        return err

    try:
        if report_id.strip():
            report = client.report.read(id=report_id.strip())
            if report is None:
                return json.dumps({
                    "tool": "opencti_get_report",
                    "report_id": report_id,
                    "error": True,
                    "message": f"Report not found: {report_id}",
                }, indent=2, default=str)
            return json.dumps({
                "tool": "opencti_get_report",
                "report_id": report_id,
                "result": report,
            }, indent=2, default=str)

        reports = client.report.list(
            search=query if query.strip() else None,
            first=limit,
        )
        return json.dumps({
            "tool": "opencti_get_report",
            "query": query,
            "count": len(reports),
            "results": reports,
        }, indent=2, default=str)
    except Exception as exc:
        logger.error("opencti_get_report failed: %s", exc)
        return json.dumps({
            "error": True,
            "message": "Failed to get/search reports",
            "detail": str(exc),
        }, indent=2, default=str)


@mcp.tool()
async def opencti_list_attack_patterns(
    query: str = "",
    limit: int = 20,
) -> str:
    """List MITRE ATT&CK techniques (attack patterns) from OpenCTI.

    Returns matching ATT&CK techniques with IDs, names, and descriptions.

    Args:
        query: Optional search query to filter attack patterns.
        limit: Maximum number of results to return (default 20).
    """
    logger.info("opencti_list_attack_patterns query=%s limit=%d", query, limit)

    client, err = _get_client()
    if err:
        return err

    try:
        patterns = client.attack_pattern.list(
            search=query if query.strip() else None,
            first=limit,
        )
        return json.dumps({
            "tool": "opencti_list_attack_patterns",
            "query": query,
            "count": len(patterns),
            "results": patterns,
        }, indent=2, default=str)
    except Exception as exc:
        logger.error("opencti_list_attack_patterns failed: %s", exc)
        return json.dumps({
            "error": True,
            "message": "Failed to list attack patterns",
            "detail": str(exc),
        }, indent=2, default=str)


def main():
    logger.info("Starting opencti-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
