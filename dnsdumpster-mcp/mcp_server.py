#!/usr/bin/env python3
"""DNSDumpster MCP Server — Passive DNS reconnaissance with subdomain enumeration.

Wraps the dnsdumpster CLI (nmmapper/dnsdumpster) to expose passive DNS
reconnaissance capabilities through the Model Context Protocol (MCP).

DNSDumpster queries multiple data sources including DNSDumpster.com, Netcraft,
VirusTotal, and SSL Certificate Transparency (crt.sh) to discover subdomains,
DNS records (A, MX, NS, TXT), ASN information, geolocation, and server types.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("dnsdumpster-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8216"))

mcp = FastMCP(
    "DNSDumpster MCP Server",
    instructions=(
        "Passive DNS reconnaissance tool. Discovers subdomains, DNS records "
        "(A, MX, NS, TXT), ASN information, geolocation, and server types "
        "by querying multiple passive data sources. No direct queries to the "
        "target — safe for initial reconnaissance."
    ),
)

BIN_NAME = os.environ.get("DNSDUMPSTER_BIN", "dnsdumpster")

DOMAIN_RE = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*"
    r"\.[a-zA-Z]{2,}$"
)


def _find_binary() -> str:
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error("dnsdumpster binary not found on PATH")
        raise FileNotFoundError(
            f"dnsdumpster binary not found. Ensure it is installed and available "
            f"on PATH, or set DNSDUMPSTER_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    binary_path = _find_binary()
    cmd = [binary_path] + args

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


def _extract_json(output: str) -> dict | None:
    """Extract a JSON object from output that may contain non-JSON preamble."""
    start = output.find("{")
    end = output.rfind("}") + 1
    if start == -1 or end == 0:
        return None
    try:
        return json.loads(output[start:end])
    except json.JSONDecodeError:
        return None


def _normalize_asn(asn_info) -> dict | None:
    """Normalize ASN info into a consistent dict with string values."""
    if not asn_info:
        return None
    if isinstance(asn_info, dict):
        return {
            "asn": str(asn_info.get("asn", "")),
            "asn_cidr": str(asn_info.get("asn_cidr", "")),
            "asn_country_code": str(asn_info.get("asn_country_code", "")),
            "asn_date": str(asn_info.get("asn_date", "")),
            "asn_description": str(asn_info.get("asn_description", "")),
            "asn_registry": str(asn_info.get("asn_registry", "")),
        }
    return None


@mcp.tool()
async def dnsdumpster_search(
    domain: str,
    timeout_seconds: int = 300,
) -> str:
    """Perform comprehensive passive DNS reconnaissance on a target domain.

    Discovers subdomains, DNS records (A, MX, NS, TXT), ASN information,
    geolocation data, and server types by querying DNSDumpster, Netcraft,
    VirusTotal, and SSL Certificate Transparency logs. This is passive
    reconnaissance — no direct queries are sent to the target domain.

    Args:
        domain: Target domain name (e.g. "example.com"). Protocols are
            stripped automatically if present.
        timeout_seconds: Maximum execution time in seconds (default 300).
    """
    logger.info("dnsdumpster_search called with domain=%s", domain)

    domain = domain.strip()
    if domain.startswith(("http://", "https://")):
        from urllib.parse import urlparse
        parsed = urlparse(domain)
        domain = parsed.netloc or parsed.path
    domain = domain.rstrip("/").strip()

    if not domain or not DOMAIN_RE.match(domain):
        return json.dumps({
            "status": "error",
            "message": f"Invalid domain format: {domain!r}. Expected: example.com",
        })

    result = await _run_command(["-d", domain], timeout_seconds=timeout_seconds)

    if result["return_code"] != 0 and result["return_code"] != -1:
        detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps({
            "status": "error",
            "message": f"dnsdumpster failed (exit {result['return_code']})",
            "detail": detail.strip(),
        }, indent=2)

    if result["return_code"] == -1:
        return json.dumps({
            "status": "error",
            "message": result["stderr"],
        }, indent=2)

    dns_records = _extract_json(result["stdout"])
    if dns_records is None:
        return json.dumps({
            "status": "error",
            "message": "No valid JSON in dnsdumpster output",
            "raw_output": result["stdout"][:500] if result["stdout"] else "",
            "stderr": result["stderr"][:500] if result["stderr"] else "",
        }, indent=2)

    output = {
        "status": "success",
        "host": dns_records.get("host", domain),
        "server": dns_records.get("server", ""),
        "mx": [],
        "ns": [],
        "txt": [],
        "asn": _normalize_asn(dns_records.get("asn")),
        "subdomains": [],
        "subdomain_count": 0,
        "mx_count": 0,
        "ns_count": 0,
        "txt_count": 0,
    }

    for mx in dns_records.get("mx", []) or []:
        if isinstance(mx, dict):
            output["mx"].append({
                "preference": int(mx.get("preference", 0) or 0),
                "exchange": str(mx.get("exchange", "")).rstrip("."),
            })
        elif isinstance(mx, str):
            output["mx"].append({"preference": 0, "exchange": mx.rstrip(".")})

    for ns in dns_records.get("ns", []) or []:
        if isinstance(ns, dict):
            entry = {"target": str(ns.get("target") or ns.get("ns") or "").rstrip(".")}
            if ns.get("ip"):
                entry["ip"] = str(ns["ip"]).strip()
            output["ns"].append(entry)
        elif isinstance(ns, str):
            output["ns"].append({"target": ns.rstrip(".")})

    txt_records = dns_records.get("txt", []) or []
    if isinstance(txt_records, str):
        txt_records = [txt_records]
    output["txt"] = [str(t).strip() for t in txt_records if t]

    for sub in dns_records.get("subdomains", []) or []:
        if isinstance(sub, dict):
            name = str(sub.get("subdomain", "")).strip()
            if not name:
                continue
            output["subdomains"].append({
                "subdomain": name,
                "subdomain_ip": str(sub.get("subdomain_ip", "")).strip(),
                "server": str(sub.get("server", "")).strip(),
                "asn": _normalize_asn(sub.get("asn")),
            })

    output["subdomain_count"] = len(output["subdomains"])
    output["mx_count"] = len(output["mx"])
    output["ns_count"] = len(output["ns"])
    output["txt_count"] = len(output["txt"])

    logger.info(
        "dnsdumpster_search complete: domain=%s subdomains=%d mx=%d ns=%d txt=%d",
        domain, output["subdomain_count"], output["mx_count"],
        output["ns_count"], output["txt_count"],
    )
    return json.dumps(output, indent=2, default=str)


@mcp.tool()
async def run_dnsdumpster(
    arguments: str,
    timeout_seconds: int = 300,
) -> str:
    """Run the dnsdumpster CLI with arbitrary arguments.

    Use this for direct CLI access. The primary flag is: -d DOMAIN

    Args:
        arguments: Command-line arguments string (e.g. "-d example.com").
        timeout_seconds: Maximum execution time in seconds (default 300).
    """
    import shlex

    logger.info("run_dnsdumpster called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("dnsdumpster failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps({
            "error": True,
            "message": f"dnsdumpster failed (exit code {result['return_code']})",
            "detail": error_detail.strip(),
            "command": f"dnsdumpster {' '.join(args)}",
        }, indent=2)

    stdout = result["stdout"].strip()
    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    parsed = _extract_json(stdout)
    if parsed:
        return json.dumps(parsed, indent=2, default=str)

    results = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            results.append({"raw": line})

    if len(results) == 1:
        return json.dumps(results[0], indent=2)
    return json.dumps(results, indent=2)


def main():
    logger.info("Starting dnsdumpster-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
