#!/usr/bin/env python3
"""MISP MCP Server — Threat intelligence sharing platform (IOC search, event management).

Queries the MISP REST API to expose threat intelligence
capabilities through the Model Context Protocol (MCP).
"""

import json
import logging
import os
import sys

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("misp-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8371"))

mcp = FastMCP(
    "MISP MCP Server",
    instructions=(
        "Threat intelligence sharing platform. Search IOCs, browse events, "
        "and add attributes via the MISP REST API."
    ),
)


def _get_config() -> tuple[str, str] | dict:
    """Return (api_key, base_url) or an error dict if not configured."""
    api_key = os.environ.get("MISP_API_KEY", "").strip()
    base_url = os.environ.get("MISP_URL", "").strip().rstrip("/")
    if not api_key or not base_url:
        missing = []
        if not api_key:
            missing.append("MISP_API_KEY")
        if not base_url:
            missing.append("MISP_URL")
        return {
            "error": True,
            "message": f"Missing required environment variable(s): {', '.join(missing)}",
            "hint": "Set MISP_API_KEY and MISP_URL environment variables.",
        }
    return api_key, base_url


def _headers(api_key: str) -> dict:
    return {
        "Authorization": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _handle_response(resp: requests.Response) -> dict:
    """Parse a MISP API response, handling common error codes."""
    if resp.status_code == 401:
        return {"error": True, "message": "Authentication failed (401). Check MISP_API_KEY."}
    if resp.status_code == 403:
        return {"error": True, "message": "Access forbidden (403). Insufficient permissions."}
    if resp.status_code == 404:
        return {"error": True, "message": "Resource not found (404)."}
    try:
        return resp.json()
    except (ValueError, requests.exceptions.JSONDecodeError):
        return {"status_code": resp.status_code, "body": resp.text[:2000]}


@mcp.tool()
def misp_search_attributes(
    value: str,
    type_attribute: str = "",
    limit: int = 25,
) -> str:
    """Search MISP attributes (IOCs) by value.

    Queries the MISP restSearch endpoint to find indicators of compromise
    matching the given value (IP, domain, hash, email, etc.).

    Args:
        value: The IOC value to search for (e.g. "8.8.8.8", "evil.com", a hash).
        type_attribute: Optional MISP attribute type filter (e.g. "ip-dst", "domain", "md5").
        limit: Maximum number of results to return (default 25).
    """
    logger.info("misp_search_attributes called: value=%s type=%s limit=%d", value, type_attribute, limit)
    cfg = _get_config()
    if isinstance(cfg, dict):
        return json.dumps(cfg, indent=2)
    api_key, base_url = cfg

    payload: dict = {"returnFormat": "json", "value": value, "limit": limit}
    if type_attribute:
        payload["type"] = type_attribute

    try:
        resp = requests.post(
            f"{base_url}/attributes/restSearch",
            headers=_headers(api_key),
            json=payload,
            verify=False,
            timeout=60,
        )
        return json.dumps(_handle_response(resp), indent=2)
    except requests.exceptions.Timeout:
        return json.dumps({"error": True, "message": "Request timed out after 60s."}, indent=2)
    except requests.exceptions.ConnectionError as exc:
        return json.dumps({"error": True, "message": f"Connection error: {exc}"}, indent=2)
    except Exception as exc:
        logger.error("misp_search_attributes failed: %s", exc)
        return json.dumps({"error": True, "message": str(exc)}, indent=2)


@mcp.tool()
def misp_search_events(
    query: str,
    limit: int = 25,
) -> str:
    """Search MISP events by keyword.

    Searches event info fields for the given query string.

    Args:
        query: Search term to match against event info/descriptions.
        limit: Maximum number of results to return (default 25).
    """
    logger.info("misp_search_events called: query=%s limit=%d", query, limit)
    cfg = _get_config()
    if isinstance(cfg, dict):
        return json.dumps(cfg, indent=2)
    api_key, base_url = cfg

    payload = {"returnFormat": "json", "eventinfo": query, "limit": limit}

    try:
        resp = requests.post(
            f"{base_url}/events/restSearch",
            headers=_headers(api_key),
            json=payload,
            verify=False,
            timeout=60,
        )
        return json.dumps(_handle_response(resp), indent=2)
    except requests.exceptions.Timeout:
        return json.dumps({"error": True, "message": "Request timed out after 60s."}, indent=2)
    except requests.exceptions.ConnectionError as exc:
        return json.dumps({"error": True, "message": f"Connection error: {exc}"}, indent=2)
    except Exception as exc:
        logger.error("misp_search_events failed: %s", exc)
        return json.dumps({"error": True, "message": str(exc)}, indent=2)


@mcp.tool()
def misp_get_event(
    event_id: str,
) -> str:
    """Get a specific MISP event by ID.

    Retrieves full event details including all attributes and metadata.

    Args:
        event_id: The numeric MISP event ID (e.g. "1234").
    """
    logger.info("misp_get_event called: event_id=%s", event_id)
    cfg = _get_config()
    if isinstance(cfg, dict):
        return json.dumps(cfg, indent=2)
    api_key, base_url = cfg

    try:
        resp = requests.get(
            f"{base_url}/events/view/{event_id}",
            headers=_headers(api_key),
            verify=False,
            timeout=60,
        )
        return json.dumps(_handle_response(resp), indent=2)
    except requests.exceptions.Timeout:
        return json.dumps({"error": True, "message": "Request timed out after 60s."}, indent=2)
    except requests.exceptions.ConnectionError as exc:
        return json.dumps({"error": True, "message": f"Connection error: {exc}"}, indent=2)
    except Exception as exc:
        logger.error("misp_get_event failed: %s", exc)
        return json.dumps({"error": True, "message": str(exc)}, indent=2)


@mcp.tool()
def misp_add_attribute(
    event_id: str,
    type_attribute: str,
    value: str,
    category: str = "Network activity",
) -> str:
    """Add an attribute (IOC) to an existing MISP event.

    Creates a new attribute on the specified event. Use this to enrich
    events with additional indicators of compromise.

    Args:
        event_id: The numeric MISP event ID to add the attribute to.
        type_attribute: MISP attribute type (e.g. "ip-dst", "domain", "md5", "url").
        value: The attribute value (e.g. "192.168.1.1", "evil.com").
        category: MISP category (default "Network activity"). Common values:
                  "Network activity", "Payload delivery", "External analysis".
    """
    logger.info("misp_add_attribute called: event=%s type=%s value=%s", event_id, type_attribute, value)
    cfg = _get_config()
    if isinstance(cfg, dict):
        return json.dumps(cfg, indent=2)
    api_key, base_url = cfg

    payload = {
        "type": type_attribute,
        "value": value,
        "category": category,
    }

    try:
        resp = requests.post(
            f"{base_url}/attributes/add/{event_id}",
            headers=_headers(api_key),
            json=payload,
            verify=False,
            timeout=60,
        )
        return json.dumps(_handle_response(resp), indent=2)
    except requests.exceptions.Timeout:
        return json.dumps({"error": True, "message": "Request timed out after 60s."}, indent=2)
    except requests.exceptions.ConnectionError as exc:
        return json.dumps({"error": True, "message": f"Connection error: {exc}"}, indent=2)
    except Exception as exc:
        logger.error("misp_add_attribute failed: %s", exc)
        return json.dumps({"error": True, "message": str(exc)}, indent=2)


def main():
    logger.info("Starting misp-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
