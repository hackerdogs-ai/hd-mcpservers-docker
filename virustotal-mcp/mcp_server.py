#!/usr/bin/env python3
"""VirusTotal MCP Server — File, URL, domain & IP threat intelligence via VT API v3.

Queries the VirusTotal REST API v3 to retrieve threat reports and submit
URLs for scanning, exposed through the Model Context Protocol (MCP).
"""

import base64
import json
import logging
import os
import sys

import requests
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("virustotal-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8369"))

VT_BASE_URL = "https://www.virustotal.com/api/v3"

mcp = FastMCP(
    "VirusTotal MCP Server",
    instructions=(
        "File, URL, domain & IP threat intelligence via VirusTotal API v3. "
        "Requires the VT_API_KEY environment variable."
    ),
)


def _get_api_key() -> str | None:
    return os.environ.get("VT_API_KEY") or None


def _headers(api_key: str) -> dict:
    return {"x-apikey": api_key, "Accept": "application/json"}


def _error(message: str) -> str:
    return json.dumps({"error": True, "message": message}, indent=2)


def _compute_verdict(stats: dict) -> str:
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    undetected = stats.get("undetected", 0)
    harmless = stats.get("harmless", 0)
    total = malicious + suspicious + undetected + harmless
    if total == 0:
        return "unknown"
    if malicious >= 5:
        return "malicious"
    if malicious >= 1 or suspicious >= 3:
        return "suspicious"
    return "clean"


def _do_get(endpoint: str, api_key: str) -> dict:
    """Perform a GET request to the VT API and return parsed JSON or error dict."""
    url = f"{VT_BASE_URL}{endpoint}"
    try:
        resp = requests.get(url, headers=_headers(api_key), timeout=30)
    except requests.exceptions.Timeout:
        return {"error": True, "message": f"Request timed out: GET {endpoint}"}
    except requests.exceptions.RequestException as exc:
        return {"error": True, "message": f"Request failed: {exc}"}

    if resp.status_code == 401:
        return {"error": True, "message": "Invalid API key (HTTP 401). Check VT_API_KEY."}
    if resp.status_code == 404:
        return {"error": True, "message": f"Resource not found (HTTP 404): {endpoint}"}
    if resp.status_code != 200:
        return {"error": True, "message": f"VT API error (HTTP {resp.status_code})", "detail": resp.text[:500]}

    return resp.json()


def _do_post(endpoint: str, api_key: str, data: dict | None = None) -> dict:
    """Perform a POST request to the VT API and return parsed JSON or error dict."""
    url = f"{VT_BASE_URL}{endpoint}"
    try:
        resp = requests.post(url, headers=_headers(api_key), data=data, timeout=30)
    except requests.exceptions.Timeout:
        return {"error": True, "message": f"Request timed out: POST {endpoint}"}
    except requests.exceptions.RequestException as exc:
        return {"error": True, "message": f"Request failed: {exc}"}

    if resp.status_code == 401:
        return {"error": True, "message": "Invalid API key (HTTP 401). Check VT_API_KEY."}
    if resp.status_code not in (200, 201):
        return {"error": True, "message": f"VT API error (HTTP {resp.status_code})", "detail": resp.text[:500]}

    return resp.json()


@mcp.tool()
def vt_file_report(file_hash: str) -> str:
    """Get the VirusTotal analysis report for a file by its hash (MD5, SHA-1, or SHA-256).

    Args:
        file_hash: MD5, SHA-1, or SHA-256 hash of the file.
    """
    logger.info("vt_file_report called with hash=%s", file_hash)
    api_key = _get_api_key()
    if not api_key:
        return _error("VT_API_KEY environment variable is not set.")

    result = _do_get(f"/files/{file_hash}", api_key)
    if result.get("error"):
        return json.dumps(result, indent=2)

    attrs = result.get("data", {}).get("attributes", {})
    stats = attrs.get("last_analysis_stats", {})
    return json.dumps({
        "hash": file_hash,
        "sha256": attrs.get("sha256"),
        "file_name": attrs.get("meaningful_name") or attrs.get("names", [None])[0] if attrs.get("names") else None,
        "file_type": attrs.get("type_description"),
        "size": attrs.get("size"),
        "verdict": _compute_verdict(stats),
        "stats": stats,
        "reputation": attrs.get("reputation"),
        "tags": attrs.get("tags", []),
        "first_seen": attrs.get("first_submission_date"),
        "last_analysis_date": attrs.get("last_analysis_date"),
    }, indent=2)


@mcp.tool()
def vt_url_report(url: str) -> str:
    """Get the VirusTotal analysis report for a URL.

    Args:
        url: The URL to look up (e.g. https://example.com/path).
    """
    logger.info("vt_url_report called with url=%s", url)
    api_key = _get_api_key()
    if not api_key:
        return _error("VT_API_KEY environment variable is not set.")

    url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    result = _do_get(f"/urls/{url_id}", api_key)
    if result.get("error"):
        return json.dumps(result, indent=2)

    attrs = result.get("data", {}).get("attributes", {})
    stats = attrs.get("last_analysis_stats", {})
    return json.dumps({
        "url": url,
        "final_url": attrs.get("last_final_url"),
        "verdict": _compute_verdict(stats),
        "stats": stats,
        "reputation": attrs.get("reputation"),
        "categories": attrs.get("categories", {}),
        "title": attrs.get("title"),
        "last_analysis_date": attrs.get("last_analysis_date"),
    }, indent=2)


@mcp.tool()
def vt_domain_report(domain: str) -> str:
    """Get the VirusTotal analysis report for a domain.

    Args:
        domain: Domain name to look up (e.g. example.com).
    """
    logger.info("vt_domain_report called with domain=%s", domain)
    api_key = _get_api_key()
    if not api_key:
        return _error("VT_API_KEY environment variable is not set.")

    result = _do_get(f"/domains/{domain}", api_key)
    if result.get("error"):
        return json.dumps(result, indent=2)

    attrs = result.get("data", {}).get("attributes", {})
    stats = attrs.get("last_analysis_stats", {})
    return json.dumps({
        "domain": domain,
        "verdict": _compute_verdict(stats),
        "stats": stats,
        "reputation": attrs.get("reputation"),
        "registrar": attrs.get("registrar"),
        "creation_date": attrs.get("creation_date"),
        "categories": attrs.get("categories", {}),
        "whois": attrs.get("whois", "")[:500],
        "last_analysis_date": attrs.get("last_analysis_date"),
        "tags": attrs.get("tags", []),
    }, indent=2)


@mcp.tool()
def vt_ip_report(ip_address: str) -> str:
    """Get the VirusTotal analysis report for an IP address.

    Args:
        ip_address: IPv4 or IPv6 address to look up.
    """
    logger.info("vt_ip_report called with ip=%s", ip_address)
    api_key = _get_api_key()
    if not api_key:
        return _error("VT_API_KEY environment variable is not set.")

    result = _do_get(f"/ip_addresses/{ip_address}", api_key)
    if result.get("error"):
        return json.dumps(result, indent=2)

    attrs = result.get("data", {}).get("attributes", {})
    stats = attrs.get("last_analysis_stats", {})
    return json.dumps({
        "ip_address": ip_address,
        "verdict": _compute_verdict(stats),
        "stats": stats,
        "reputation": attrs.get("reputation"),
        "as_owner": attrs.get("as_owner"),
        "asn": attrs.get("asn"),
        "country": attrs.get("country"),
        "network": attrs.get("network"),
        "last_analysis_date": attrs.get("last_analysis_date"),
        "tags": attrs.get("tags", []),
    }, indent=2)


@mcp.tool()
def vt_scan_url(url: str) -> str:
    """Submit a URL to VirusTotal for scanning.

    Returns an analysis ID that can be checked with vt_get_analysis.

    Args:
        url: The URL to submit for scanning.
    """
    logger.info("vt_scan_url called with url=%s", url)
    api_key = _get_api_key()
    if not api_key:
        return _error("VT_API_KEY environment variable is not set.")

    result = _do_post("/urls", api_key, data={"url": url})
    if result.get("error"):
        return json.dumps(result, indent=2)

    data = result.get("data", {})
    analysis_id = data.get("id", "")
    return json.dumps({
        "url": url,
        "analysis_id": analysis_id,
        "type": data.get("type"),
        "message": "URL submitted for scanning. Use vt_get_analysis with the analysis_id to check results.",
    }, indent=2)


@mcp.tool()
def vt_get_analysis(analysis_id: str) -> str:
    """Get the status and results of a VirusTotal analysis by its ID.

    Use this to check the result of a URL scan submitted via vt_scan_url.

    Args:
        analysis_id: The analysis ID returned by vt_scan_url or other submission endpoints.
    """
    logger.info("vt_get_analysis called with id=%s", analysis_id)
    api_key = _get_api_key()
    if not api_key:
        return _error("VT_API_KEY environment variable is not set.")

    result = _do_get(f"/analyses/{analysis_id}", api_key)
    if result.get("error"):
        return json.dumps(result, indent=2)

    attrs = result.get("data", {}).get("attributes", {})
    stats = attrs.get("stats", {})
    return json.dumps({
        "analysis_id": analysis_id,
        "status": attrs.get("status"),
        "verdict": _compute_verdict(stats),
        "stats": stats,
        "date": attrs.get("date"),
    }, indent=2)


def main():
    logger.info("Starting virustotal-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
