"""TLSx MCP Server - TLS Certificate & Configuration Scanning via FastMCP."""

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
logger = logging.getLogger("tlsx-mcp")

mcp = FastMCP(
    "tlsx-mcp",
    instructions="MCP server for TLSx - fast TLS grabber for certificate data collection, TLS configuration analysis, and misconfiguration detection.",
)

TLSX_BIN = shutil.which("tlsx") or "tlsx"


def _run_tlsx(args: list[str], timeout: int = 120) -> dict:
    """Execute tlsx CLI and return structured result."""
    try:
        result = subprocess.run(
            [TLSX_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("tlsx exited with code %d: %s", result.returncode, stderr)

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
        logger.error("tlsx binary not found at '%s'", TLSX_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"tlsx binary not found at '{TLSX_BIN}'. Ensure tlsx is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("tlsx command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"tlsx command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("tlsx command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def scan_tls(
    hosts: str,
    ports: str = "443",
    show_san: bool = True,
    show_cn: bool = True,
    show_org: bool = False,
    tls_version: bool = False,
    cipher: bool = False,
    jarm: bool = False,
    ja3: bool = False,
    enumerate_versions: bool = False,
    enumerate_ciphers: bool = False,
) -> dict:
    """Scan TLS configuration and certificate data for one or more targets.

    Collects certificate details including subject, issuer, SANs, validity,
    TLS version, cipher suites, JARM fingerprint, and JA3 hash.

    Args:
        hosts: Comma-separated list of targets (IP, hostname, CIDR, URL, ASN).
        ports: Comma-separated ports to scan. Default "443".
        show_san: Show Subject Alternative Names. Default True.
        show_cn: Show Common Name. Default True.
        show_org: Show Subject Organization. Default False.
        tls_version: Show TLS version in output. Default False.
        cipher: Show cipher suite in output. Default False.
        jarm: Compute JARM fingerprint. Default False.
        ja3: Compute JA3 hash. Default False.
        enumerate_versions: Enumerate all supported TLS versions. Default False.
        enumerate_ciphers: Enumerate all supported cipher suites. Default False.

    Returns:
        Dictionary with TLS scan results for each target.
    """
    logger.info("scan_tls called with hosts=%s", hosts)
    args = ["-json"]

    for host in hosts.split(","):
        host = host.strip()
        if host:
            args.extend(["-u", host])

    if ports and ports != "443":
        args.extend(["-p", ports])

    if show_san:
        args.append("-san")
    if show_cn:
        args.append("-cn")
    if show_org:
        args.append("-so")
    if tls_version:
        args.append("-tv")
    if cipher:
        args.append("-cipher")
    if jarm:
        args.append("-jarm")
    if ja3:
        args.append("-ja3")
    if enumerate_versions:
        args.append("-ve")
    if enumerate_ciphers:
        args.append("-ce")

    return _run_tlsx(args)


@mcp.tool()
def check_misconfigurations(
    hosts: str,
    check_expired: bool = True,
    check_self_signed: bool = True,
    check_mismatched: bool = True,
) -> dict:
    """Check for TLS certificate misconfigurations on one or more targets.

    Detects expired certificates, self-signed certificates, and hostname
    mismatches that indicate potential security issues.

    Args:
        hosts: Comma-separated list of targets (IP, hostname, CIDR, URL, ASN).
        check_expired: Check for expired certificates. Default True.
        check_self_signed: Check for self-signed certificates. Default True.
        check_mismatched: Check for hostname mismatches. Default True.

    Returns:
        Dictionary with misconfiguration detection results.
    """
    logger.info("check_misconfigurations called with hosts=%s", hosts)
    args = ["-json"]

    for host in hosts.split(","):
        host = host.strip()
        if host:
            args.extend(["-u", host])

    if check_expired:
        args.append("-ex")
    if check_self_signed:
        args.append("-ss")
    if check_mismatched:
        args.append("-mm")

    return _run_tlsx(args)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8109"))
    logger.info("Starting tlsx-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
