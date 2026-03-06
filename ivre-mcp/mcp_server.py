"""IVRE MCP Server - Network Reconnaissance Query Interface via FastMCP.

Connects to an existing IVRE deployment's Web API to expose network
reconnaissance data (active scans, passive recon, passive DNS, flows,
IP geolocation) as MCP tools.
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
logger = logging.getLogger("ivre-mcp")

IVRE_WEB_URL = os.environ.get("IVRE_WEB_URL", "").rstrip("/")
IVRE_VERIFY_SSL = os.environ.get("IVRE_VERIFY_SSL", "true").lower() not in ("false", "0", "no")
MAX_RESULTS_IN_RESPONSE = 200

_http_client: httpx.AsyncClient | None = None

mcp = FastMCP(
    "ivre-mcp",
    instructions=(
        "MCP server for IVRE - a network reconnaissance framework. "
        "Queries an existing IVRE deployment to retrieve active scan results, "
        "passive reconnaissance data, passive DNS records, network flows, "
        "and IP geolocation/AS data. Requires IVRE_WEB_URL to be set. "
        "See DEPLOY_IVRE.md for how to deploy IVRE with Docker."
    ),
)


def _get_base_url() -> str:
    if not IVRE_WEB_URL:
        raise ValueError(
            "IVRE_WEB_URL environment variable is not set. "
            "Set it to the base URL of your IVRE web interface "
            "(e.g., http://ivre-web:80)."
        )
    return IVRE_WEB_URL


async def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(
            verify=IVRE_VERIFY_SSL,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
    return _http_client


def _build_query_param(limit: int | None, skip: int | None, sort: str | None) -> str | None:
    """Build the 'q' query parameter combining limit, skip, and sort directives."""
    parts = []
    if skip and skip > 0:
        parts.append(f"skip:{skip}")
    if limit and limit > 0:
        parts.append(f"limit:{limit}")
    if sort:
        parts.append(f"sortby:{sort}")
    return " ".join(parts) if parts else None


def _truncate_results(results: list, limit: int = MAX_RESULTS_IN_RESPONSE) -> tuple[list, bool]:
    """Truncate a results list and return (results, was_truncated)."""
    if len(results) <= limit:
        return results, False
    return results[:limit], True


def _parse_response_body(text: str, content_type: str) -> any:
    """Parse IVRE response body, handling JSON, NDJSON, and plain text."""
    body = text.strip()
    if not body:
        return None

    if "ndjson" in content_type or ("\n" in body and body.lstrip()[0:1] in ("{", "[")):
        lines = body.splitlines()
        results = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                results.append({"raw": line})
        return results

    try:
        return json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return body


async def _ivre_request(
    path: str,
    filter_str: str | None = None,
    limit: int | None = None,
    skip: int | None = None,
    sort: str | None = None,
    extra_params: dict | None = None,
) -> dict:
    """Make an async HTTP request to the IVRE Web API."""
    try:
        base_url = _get_base_url()
    except ValueError as exc:
        return {"success": False, "output": None, "error": str(exc)}

    url = f"{base_url}/cgi/{path.lstrip('/')}"
    params: dict[str, str] = {
        "format": "json",
        "datesasstrings": "1",
    }
    if filter_str:
        params["f"] = filter_str
    q_param = _build_query_param(limit, skip, sort)
    if q_param:
        params["q"] = q_param
    if extra_params:
        params.update(extra_params)

    logger.info("IVRE request: GET %s params=%s", url, params)

    try:
        client = await _get_client()
        resp = await client.get(url, params=params)

        if resp.status_code != 200:
            logger.warning("IVRE API returned status %d: %s", resp.status_code, resp.text[:500])
            return {
                "success": False,
                "output": None,
                "error": f"IVRE API returned HTTP {resp.status_code}: {resp.text[:500]}",
            }

        content_type = resp.headers.get("content-type", "")
        parsed = _parse_response_body(resp.text, content_type)

        if isinstance(parsed, list):
            truncated_results, was_truncated = _truncate_results(parsed)
            result: dict = {"success": True, "output": truncated_results, "count": len(parsed)}
            if was_truncated:
                result["truncated"] = True
                result["message"] = (
                    f"Showing {len(truncated_results)} of {len(parsed)} results. "
                    "Use skip/limit parameters to paginate."
                )
            return result

        return {"success": True, "output": parsed}

    except httpx.ConnectError as exc:
        logger.error("Connection to IVRE failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "error": f"Cannot connect to IVRE at {base_url}. Verify IVRE_WEB_URL and that IVRE is running.",
        }
    except httpx.TimeoutException:
        logger.error("IVRE request timed out")
        return {
            "success": False,
            "output": None,
            "error": "IVRE request timed out. The server may be overloaded or the query too broad.",
        }
    except Exception as exc:
        logger.error("IVRE request failed: %s", exc)
        return {"success": False, "output": None, "error": str(exc)}


# ---------------------------------------------------------------------------
# 1. Query Tools (core data retrieval)
# ---------------------------------------------------------------------------


@mcp.tool()
async def query_hosts(
    database: str = "view",
    filter: str = "",
    limit: int = 50,
    skip: int = 0,
    sort: str = "",
) -> dict:
    """Query hosts from the IVRE scan or view database.

    Returns full host records including open ports, services, banners,
    hostnames, OS detection, scripts output, and more.

    Args:
        database: Database to query - "scans" for raw Nmap results or "view" for the consolidated view. Default "view".
        filter: IVRE filter string. Examples: "port:22", "service:http", "hostname:example.com", "country:US", "net:10.0.0.0/8", "product:Apache". Multiple filters separated by spaces are ANDed.
        limit: Maximum number of results to return. Default 50.
        skip: Number of results to skip (for pagination). Default 0.
        sort: Sort field (e.g., "addr" for IP address). Prefix with "-" for descending.
    """
    logger.info("query_hosts: database=%s filter=%s limit=%d", database, filter, limit)
    if database not in ("scans", "view"):
        return {"success": False, "output": None, "error": "database must be 'scans' or 'view'"}
    return await _ivre_request(
        database,
        filter_str=filter or None,
        limit=limit,
        skip=skip,
        sort=sort or None,
    )


@mcp.tool()
async def count_hosts(
    database: str = "view",
    filter: str = "",
) -> dict:
    """Count hosts matching a filter in the IVRE scan or view database.

    Useful for getting an overview of how many hosts match certain criteria
    before fetching full records.

    Args:
        database: Database to query - "scans" or "view". Default "view".
        filter: IVRE filter string. Examples: "port:443", "service:ssh", "country:DE". Leave empty to count all hosts.
    """
    logger.info("count_hosts: database=%s filter=%s", database, filter)
    if database not in ("scans", "view"):
        return {"success": False, "output": None, "error": "database must be 'scans' or 'view'"}
    return await _ivre_request(
        f"{database}/count",
        filter_str=filter or None,
    )


@mcp.tool()
async def query_passive(
    filter: str = "",
    limit: int = 50,
    skip: int = 0,
    sort: str = "",
) -> dict:
    """Query passive reconnaissance records from the IVRE passive database.

    Returns passive intelligence gathered from network traffic analysis
    (Zeek, p0f, airodump-ng) including DNS answers, HTTP headers,
    SSL certificates, SSH host keys, and more.

    Args:
        filter: IVRE filter string for passive data. Examples: "sensor:MyZeek", "recontype:DNS_ANSWER".
        limit: Maximum number of results. Default 50.
        skip: Number of results to skip. Default 0.
        sort: Sort field. Prefix with "-" for descending.
    """
    logger.info("query_passive: filter=%s limit=%d", filter, limit)
    return await _ivre_request(
        "passive",
        filter_str=filter or None,
        limit=limit,
        skip=skip,
        sort=sort or None,
    )


@mcp.tool()
async def count_passive(
    filter: str = "",
) -> dict:
    """Count passive reconnaissance records matching a filter.

    Args:
        filter: IVRE filter string for passive data. Leave empty to count all records.
    """
    logger.info("count_passive: filter=%s", filter)
    return await _ivre_request(
        "passive/count",
        filter_str=filter or None,
    )


# ---------------------------------------------------------------------------
# 2. Aggregation Tools (analytics)
# ---------------------------------------------------------------------------


@mcp.tool()
async def top_values(
    database: str = "view",
    field: str = "service",
    filter: str = "",
    limit: int = 10,
) -> dict:
    """Get the most common values for a given field across hosts.

    Useful for understanding the distribution of services, ports, products,
    countries, AS numbers, etc. in your reconnaissance data.

    Args:
        database: Database to query - "scans", "view", or "passive". Default "view".
        field: Field to aggregate. Common values: "service", "port", "product", "version", "country", "city", "as", "domains", "hop", "category", "source", "cpe", "cpe.vendor", "cpe.product", "devicetype", "script.id".
        filter: IVRE filter string to narrow down hosts before aggregation.
        limit: Maximum number of top values to return. Default 10.
    """
    logger.info("top_values: database=%s field=%s filter=%s", database, field, filter)
    if database not in ("scans", "view", "passive"):
        return {"success": False, "output": None, "error": "database must be 'scans', 'view', or 'passive'"}
    return await _ivre_request(
        f"{database}/top/{field}",
        filter_str=filter or None,
        limit=limit,
    )


@mcp.tool()
async def distinct_values(
    database: str = "view",
    field: str = "service",
    filter: str = "",
) -> dict:
    """Get distinct values for a field from the IVRE database.

    Similar to top_values but returns all unique values with their counts.

    Args:
        database: Database to query - "scans", "view", or "passive". Default "view".
        field: Field to get distinct values for. Same options as top_values.
        filter: IVRE filter string to narrow the dataset.
    """
    logger.info("distinct_values: database=%s field=%s filter=%s", database, field, filter)
    if database not in ("scans", "view", "passive"):
        return {"success": False, "output": None, "error": "database must be 'scans', 'view', or 'passive'"}
    return await _ivre_request(
        f"{database}/distinct/{field}",
        filter_str=filter or None,
    )


# ---------------------------------------------------------------------------
# 3. Specialized Query Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_host_ips(
    database: str = "view",
    filter: str = "",
    limit: int = 100,
    skip: int = 0,
) -> dict:
    """Get only IP addresses matching a filter (compact output).

    Returns a lightweight list of IPs instead of full host records.
    Useful for generating target lists or getting a quick overview.

    Args:
        database: Database to query - "scans" or "view". Default "view".
        filter: IVRE filter string. Examples: "port:80", "service:ssh country:FR".
        limit: Maximum number of IPs. Default 100.
        skip: Number to skip for pagination. Default 0.
    """
    logger.info("get_host_ips: database=%s filter=%s limit=%d", database, filter, limit)
    if database not in ("scans", "view"):
        return {"success": False, "output": None, "error": "database must be 'scans' or 'view'"}
    return await _ivre_request(
        f"{database}/onlyips",
        filter_str=filter or None,
        limit=limit,
        skip=skip,
    )


@mcp.tool()
async def get_ips_ports(
    database: str = "view",
    filter: str = "",
    limit: int = 100,
    skip: int = 0,
) -> dict:
    """Get IP addresses with their open ports.

    Returns a compact mapping of IPs to their open ports. More detail
    than get_host_ips but less than query_hosts.

    Args:
        database: Database to query - "scans" or "view". Default "view".
        filter: IVRE filter string. Examples: "service:http", "port:22 port:80".
        limit: Maximum number of results. Default 100.
        skip: Number to skip for pagination. Default 0.
    """
    logger.info("get_ips_ports: database=%s filter=%s limit=%d", database, filter, limit)
    if database not in ("scans", "view"):
        return {"success": False, "output": None, "error": "database must be 'scans' or 'view'"}
    return await _ivre_request(
        f"{database}/ipsports",
        filter_str=filter or None,
        limit=limit,
        skip=skip,
    )


@mcp.tool()
async def get_timeline(
    database: str = "view",
    filter: str = "",
) -> dict:
    """Get scan timeline data for time-series analysis.

    Returns temporal distribution of scan results, useful for
    understanding when hosts were scanned or when changes occurred.

    Args:
        database: Database to query - "scans" or "view". Default "view".
        filter: IVRE filter string to narrow the timeline scope.
    """
    logger.info("get_timeline: database=%s filter=%s", database, filter)
    if database not in ("scans", "view"):
        return {"success": False, "output": None, "error": "database must be 'scans' or 'view'"}
    return await _ivre_request(
        f"{database}/timeline",
        filter_str=filter or None,
    )


# ---------------------------------------------------------------------------
# 4. Enrichment Tools
# ---------------------------------------------------------------------------


@mcp.tool()
async def ip_data(
    address: str,
) -> dict:
    """Get geolocation and AS number data for a specific IP address.

    Returns estimated geographical location (country, region, city,
    coordinates) and Autonomous System information (AS number, name).

    Args:
        address: The IP address to look up (e.g., "8.8.8.8").
    """
    logger.info("ip_data: address=%s", address)
    if not address:
        return {"success": False, "output": None, "error": "address is required"}
    return await _ivre_request(f"ipdata/{address}")


@mcp.tool()
async def passive_dns(
    query: str,
    include_subdomains: bool = False,
    reverse: bool = False,
    dns_type: str = "",
) -> dict:
    """Query passive DNS records from the IVRE database.

    Compatible with the Common Output Format (RFC draft). Returns DNS
    resolution history including first/last seen timestamps, record types,
    and sensor information.

    Args:
        query: IP address or domain name to look up (e.g., "example.com" or "93.184.216.34").
        include_subdomains: If True and querying a domain, also return records for all subdomains.
        reverse: If True and querying a domain, return records pointing TO this domain (CNAME, NS, MX).
        dns_type: DNS record type filter (e.g., "A", "AAAA", "CNAME", "MX", "NS", "TXT").
    """
    logger.info("passive_dns: query=%s subdomains=%s reverse=%s", query, include_subdomains, reverse)
    if not query:
        return {"success": False, "output": None, "error": "query is required"}

    extra: dict[str, str] = {}
    if include_subdomains:
        extra["subdomains"] = "1"
    if reverse:
        extra["reverse"] = "1"
    if dns_type:
        extra["type"] = dns_type

    return await _ivre_request(f"passivedns/{query}", extra_params=extra if extra else None)


@mcp.tool()
async def query_flows(
    query: str = "",
    action: str = "",
) -> dict:
    """Query aggregated network flow data from the IVRE flow database.

    Returns network flow information including source/destination IPs,
    ports, protocols, byte/packet counts, and temporal data.

    Args:
        query: Flow query string with filters and options (limit, skip, orderby, etc.).
        action: Set to "details" to get detailed flow information.
    """
    logger.info("query_flows: query=%s action=%s", query, action)
    extra: dict[str, str] = {}
    if query:
        extra["q"] = query
    if action:
        extra["action"] = action
    return await _ivre_request("flows", extra_params=extra if extra else None)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8366"))

    if not IVRE_WEB_URL:
        logger.warning(
            "IVRE_WEB_URL is not set. Tools will return errors until it is configured. "
            "Set it to the base URL of your IVRE web interface (e.g., http://ivre-web:80)."
        )
    else:
        logger.info("IVRE Web API target: %s", IVRE_WEB_URL)

    logger.info("Starting ivre-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
