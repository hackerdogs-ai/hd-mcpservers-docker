#!/usr/bin/env python3
"""AlienVault OTX MCP Server — Threat intelligence via OTX API.

Uses the OTXv2 Python SDK to query AlienVault Open Threat Exchange
for indicators of compromise (IoCs) through the Model Context Protocol (MCP).
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
logger = logging.getLogger("otx-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8368"))

mcp = FastMCP(
    "AlienVault OTX MCP Server",
    instructions=(
        "Threat intelligence lookups via AlienVault OTX API. "
        "Query file hashes, URLs, domains, and IP addresses for threat data."
    ),
)

OTX_SERVER = "https://otx.alienvault.com"


def _get_otx_client():
    """Create and return an OTXv2 client, or None with an error dict if the key is missing."""
    api_key = os.environ.get("OTX_API_KEY", "").strip()
    if not api_key:
        return None, {
            "error": True,
            "message": "OTX_API_KEY environment variable is not set. "
            "Get a free API key at https://otx.alienvault.com",
        }
    from OTXv2 import OTXv2
    return OTXv2(api_key, server=OTX_SERVER), None


def _detect_hash_type(file_hash: str) -> str:
    """Detect hash type from length."""
    h = file_hash.strip()
    if len(h) == 32:
        return "md5"
    elif len(h) == 40:
        return "sha1"
    elif len(h) == 64:
        return "sha256"
    return "unknown"


@mcp.tool()
async def otx_file_report(file_hash: str) -> str:
    """Query AlienVault OTX for a file hash (MD5, SHA1, or SHA256).

    Returns threat intelligence data including pulse references,
    malware families, and analysis results.

    Args:
        file_hash: The file hash to look up (MD5, SHA1, or SHA256).
    """
    logger.info("otx_file_report called with file_hash=%s", file_hash)

    otx, err = _get_otx_client()
    if err:
        return json.dumps(err, indent=2)

    hash_type = _detect_hash_type(file_hash)
    if hash_type == "unknown":
        return json.dumps({
            "error": True,
            "message": f"Unrecognized hash format (length {len(file_hash.strip())}). "
            "Expected MD5 (32), SHA1 (40), or SHA256 (64) characters.",
        }, indent=2)

    try:
        from OTXv2 import IndicatorTypes

        indicator_map = {
            "md5": IndicatorTypes.FILE_HASH_MD5,
            "sha1": IndicatorTypes.FILE_HASH_SHA1,
            "sha256": IndicatorTypes.FILE_HASH_SHA256,
        }
        indicator = indicator_map[hash_type]

        sections = ["general", "analysis"]
        result = {}
        for section in sections:
            try:
                data = otx.get_indicator_details_full(indicator, file_hash.strip())
                result = data
                break
            except Exception:
                data = otx.get_indicator_details_by_section(indicator, file_hash.strip(), section)
                result[section] = data

        return json.dumps({
            "hash": file_hash.strip(),
            "hash_type": hash_type,
            "data": result,
        }, indent=2, default=str)

    except Exception as exc:
        logger.error("OTX API error for file hash %s: %s", file_hash, exc)
        return json.dumps({
            "error": True,
            "message": f"OTX API error: {exc}",
            "hash": file_hash.strip(),
        }, indent=2)


@mcp.tool()
async def otx_url_report(url: str) -> str:
    """Query AlienVault OTX for a URL.

    Returns threat intelligence data including pulse references,
    associated domains/IPs, and reputation data.

    Args:
        url: The URL to look up.
    """
    logger.info("otx_url_report called with url=%s", url)

    otx, err = _get_otx_client()
    if err:
        return json.dumps(err, indent=2)

    try:
        from OTXv2 import IndicatorTypes

        result = otx.get_indicator_details_full(IndicatorTypes.URL, url)

        return json.dumps({
            "url": url,
            "data": result,
        }, indent=2, default=str)

    except Exception as exc:
        logger.error("OTX API error for URL %s: %s", url, exc)
        return json.dumps({
            "error": True,
            "message": f"OTX API error: {exc}",
            "url": url,
        }, indent=2)


@mcp.tool()
async def otx_domain_report(domain: str) -> str:
    """Query AlienVault OTX for a domain.

    Returns threat intelligence including pulse references, DNS records,
    associated malware, WHOIS data, and reputation information.

    Args:
        domain: The domain name to look up (e.g. "example.com").
    """
    logger.info("otx_domain_report called with domain=%s", domain)

    otx, err = _get_otx_client()
    if err:
        return json.dumps(err, indent=2)

    try:
        from OTXv2 import IndicatorTypes

        result = otx.get_indicator_details_full(IndicatorTypes.DOMAIN, domain)

        return json.dumps({
            "domain": domain,
            "data": result,
        }, indent=2, default=str)

    except Exception as exc:
        logger.error("OTX API error for domain %s: %s", domain, exc)
        return json.dumps({
            "error": True,
            "message": f"OTX API error: {exc}",
            "domain": domain,
        }, indent=2)


@mcp.tool()
async def otx_ip_report(ip_address: str) -> str:
    """Query AlienVault OTX for an IP address.

    Returns threat intelligence including pulse references, geolocation,
    passive DNS, associated malware, and reputation data.

    Args:
        ip_address: The IP address to look up (IPv4 or IPv6).
    """
    logger.info("otx_ip_report called with ip_address=%s", ip_address)

    otx, err = _get_otx_client()
    if err:
        return json.dumps(err, indent=2)

    try:
        from OTXv2 import IndicatorTypes

        if ":" in ip_address:
            indicator = IndicatorTypes.IPv6
        else:
            indicator = IndicatorTypes.IPv4

        result = otx.get_indicator_details_full(indicator, ip_address)

        return json.dumps({
            "ip_address": ip_address,
            "data": result,
        }, indent=2, default=str)

    except Exception as exc:
        logger.error("OTX API error for IP %s: %s", ip_address, exc)
        return json.dumps({
            "error": True,
            "message": f"OTX API error: {exc}",
            "ip_address": ip_address,
        }, indent=2)


@mcp.tool()
async def otx_submit_url(url: str) -> str:
    """Submit a URL to AlienVault OTX for analysis.

    Submits the URL to OTX for scanning and threat analysis.
    Results may take time to process.

    Args:
        url: The URL to submit for analysis.
    """
    logger.info("otx_submit_url called with url=%s", url)

    otx, err = _get_otx_client()
    if err:
        return json.dumps(err, indent=2)

    try:
        result = otx.submit_url(url)

        return json.dumps({
            "submitted_url": url,
            "result": result,
        }, indent=2, default=str)

    except Exception as exc:
        logger.error("OTX API error submitting URL %s: %s", url, exc)
        return json.dumps({
            "error": True,
            "message": f"OTX API error: {exc}",
            "url": url,
        }, indent=2)


def main():
    logger.info("Starting otx-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
