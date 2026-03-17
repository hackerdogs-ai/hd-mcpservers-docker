#!/usr/bin/env python3
"""Abuse.ch MCP Server — MalwareBazaar, URLhaus, ThreatFox.

Wraps Abuse.ch APIs (MalwareBazaar, URLhaus, ThreatFox) for threat intelligence
via the Model Context Protocol. Requires ABUSECH_API_KEY.
"""

import json
import logging
import os
import sys

import httpx
from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("abusech-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8373"))

mcp = FastMCP(
    "Abuse.ch MCP Server",
    instructions=(
        "Threat intelligence via Abuse.ch: MalwareBazaar (file hashes), "
        "URLhaus (URLs/hosts/payloads), ThreatFox (IOCs). Requires ABUSECH_API_KEY."
    ),
)

ABUSECH_API_KEY = os.environ.get("ABUSECH_API_KEY", "")

# Abuse.ch API bases (Auth-Key header required)
URLHAUS_API = "https://urlhaus-api.abuse.ch/v1"
MALWAREBAZAAR_API = "https://mb-api.abuse.ch/api/v1"
THREATFOX_API = "https://threatfox-api.abuse.ch/api/v1"


def _headers():
    if not ABUSECH_API_KEY:
        raise ValueError("ABUSECH_API_KEY is not set")
    return {"Auth-Key": ABUSECH_API_KEY, "Accept": "application/json"}


@mcp.tool()
def urlhaus_host(host: str) -> str:
    """Get URLhaus host report for a hostname or IP. Returns URLs and payload info."""
    if not host or not host.strip():
        return json.dumps({"error": "host is required"})
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                f"{URLHAUS_API}/host/",
                headers=_headers(),
                data={"host": host.strip()},
            )
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "body": e.response.text[:500]})
    except Exception as e:
        logger.exception("urlhaus_host failed")
        return json.dumps({"error": str(e)})


@mcp.tool()
def urlhaus_url(url: str) -> str:
    """Get URLhaus URL report for a URL."""
    if not url or not url.strip():
        return json.dumps({"error": "url is required"})
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                f"{URLHAUS_API}/url/",
                headers=_headers(),
                data={"url": url.strip()},
            )
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "body": e.response.text[:500]})
    except Exception as e:
        logger.exception("urlhaus_url failed")
        return json.dumps({"error": str(e)})


@mcp.tool()
def malwarebazaar_hash(sha256_hash: str) -> str:
    """Get MalwareBazaar info for a file hash (SHA256)."""
    if not sha256_hash or not sha256_hash.strip():
        return json.dumps({"error": "sha256_hash is required"})
    try:
        with httpx.Client(timeout=30.0) as client:
            r = client.post(
                f"{MALWAREBAZAAR_API}/",
                headers=_headers(),
                data={"query": "get_info", "hash": sha256_hash.strip()},
            )
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "body": e.response.text[:500]})
    except Exception as e:
        logger.exception("malwarebazaar_hash failed")
        return json.dumps({"error": str(e)})


@mcp.tool()
def threatfox_iocs(days: int = 7) -> str:
    """Get recent ThreatFox IOCs (indicators of compromise). days: 1-365."""
    if days < 1:
        days = 1
    if days > 365:
        days = 365
    try:
        with httpx.Client(timeout=60.0) as client:
            r = client.post(
                f"{THREATFOX_API}/",
                headers=_headers(),
                json={"query": "get_iocs", "days": days},
            )
            r.raise_for_status()
            return json.dumps(r.json(), indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}", "body": e.response.text[:500]})
    except Exception as e:
        logger.exception("threatfox_iocs failed")
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    logger.info("Starting abusech-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)
