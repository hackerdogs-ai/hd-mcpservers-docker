#!/usr/bin/env python3
"""Naabu MCP Server — Fast port scanning via MCP.

Wraps the naabu CLI (projectdiscovery/naabu) to expose port scanning
capabilities through the Model Context Protocol (MCP).

Naabu is a fast port scanner written in Go that performs SYN/CONNECT/UDP
scanning to enumerate valid ports for hosts in a reliable way.
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
logger = logging.getLogger("naabu-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8105"))

mcp = FastMCP(
    "Naabu MCP Server",
    instructions=(
        "Fast port scanning. Enumerates open ports on target hosts using "
        "SYN, CONNECT, or UDP scans with configurable rate and threading."
    ),
)

NAABU_BIN = os.environ.get("NAABU_BIN", "naabu")


def _find_naabu() -> str:
    """Locate the naabu binary, raising a clear error if missing."""
    path = shutil.which(NAABU_BIN)
    if path is None:
        logger.error("naabu binary not found on PATH")
        raise FileNotFoundError(
            f"naabu binary not found. Ensure it is installed and available "
            f"on PATH, or set NAABU_BIN to the full path. "
            f"Install with: go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest"
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a naabu command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    naabu = _find_naabu()
    cmd = [naabu] + args

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
async def scan_ports(
    hosts: str,
    ports: Optional[str] = None,
    top_ports: int = 100,
    scan_type: Optional[str] = None,
    passive: bool = False,
    rate: int = 1000,
    threads: int = 25,
    exclude_hosts: Optional[str] = None,
    exclude_ports: Optional[str] = None,
) -> str:
    """Scan ports on target hosts using naabu.

    Performs fast port scanning on one or more targets, returning discovered
    open ports in JSON format.

    Args:
        hosts: Target host(s) to scan — IP, CIDR, or comma-separated list.
        ports: Specific ports or ranges to scan (e.g. '80,443', '1-1024'). Omit to use top_ports.
        top_ports: Number of top ports to scan (default 100). Ignored if ports is set.
        scan_type: Scan type — 's' for SYN (requires root/cap_net_raw) or 'c' for CONNECT.
        passive: Use passive port enumeration (no active scanning).
        rate: Packets per second rate limit (default 1000).
        threads: Number of concurrent threads (default 25).
        exclude_hosts: Hosts to exclude from scan (comma-separated).
        exclude_ports: Ports to exclude from scan (comma-separated).
    """
    logger.info("scan_ports called with hosts=%s", hosts)
    args = ["-host", hosts, "-json", "-silent"]

    if ports:
        args.extend(["-p", ports])
    else:
        args.extend(["-top-ports", str(top_ports)])

    if passive:
        args.append("-passive")
    else:
        effective_scan_type = scan_type if scan_type else "c"
        args.extend(["-s", effective_scan_type])

    args.extend(["-rate", str(rate)])
    args.extend(["-c", str(threads)])

    if exclude_hosts:
        args.extend(["-eh", exclude_hosts])
    if exclude_ports:
        args.extend(["-ep", exclude_ports])

    result = await _run_command(args)

    if result["return_code"] != 0:
        logger.warning("naabu scan failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"Naabu scan failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"naabu {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Scan completed — no open ports found", "hosts": hosts})

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
    logger.info("Starting naabu-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
