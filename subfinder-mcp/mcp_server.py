#!/usr/bin/env python3
"""Subfinder MCP Server — passive subdomain enumeration.

Wraps ProjectDiscovery's subfinder CLI to expose subdomain
discovery capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shlex
import shutil
import sys

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("subfinder-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8367"))

mcp = FastMCP(
    "Subfinder MCP Server",
    instructions=(
        "Passive subdomain enumeration using ProjectDiscovery's subfinder. "
        "Discovers subdomains for a target domain by querying multiple public "
        "and private data sources without active scanning."
    ),
)

SUBFINDER_BIN = os.environ.get("SUBFINDER_BIN", "subfinder")


def _find_binary() -> str:
    """Locate the subfinder binary, raising a clear error if missing."""
    path = shutil.which(SUBFINDER_BIN)
    if path is None:
        logger.error("subfinder binary not found on PATH")
        raise FileNotFoundError(
            f"subfinder binary not found. Ensure it is installed and available "
            f"on PATH, or set SUBFINDER_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 300) -> dict:
    """Execute a subfinder command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
    binary = _find_binary()
    cmd = [binary] + args

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
async def enumerate_subdomains(
    domain: str,
    timeout: int = 120,
    sources: str = "",
    exclude_sources: str = "",
    recursive: bool = False,
    max_depth: int = 1,
    only_active: bool = False,
    resolve: bool = False,
) -> str:
    """Enumerate subdomains for a given domain using passive sources.

    Discovers subdomains by querying multiple public and private data sources
    (certificate transparency logs, search engines, DNS datasets, etc.)
    without performing active scanning against the target.

    Args:
        domain: Target domain to enumerate subdomains for (e.g. "example.com").
        timeout: Maximum time in seconds for the enumeration (default 120).
        sources: Comma-separated list of sources to use (e.g. "crtsh,hackertarget").
                 Leave empty to use all available sources.
        exclude_sources: Comma-separated list of sources to exclude.
        recursive: Enable recursive subdomain discovery on found subdomains.
        max_depth: Maximum recursion depth when recursive is enabled (default 1).
        only_active: Only return subdomains with active DNS records.
        resolve: Resolve discovered subdomains and include IP addresses.
    """
    logger.info("enumerate_subdomains called for domain=%s", domain)

    args = ["-d", domain, "-timeout", str(timeout), "-silent", "-json"]

    if sources.strip():
        args.extend(["-sources", sources.strip()])
    if exclude_sources.strip():
        args.extend(["-exclude-sources", exclude_sources.strip()])
    if recursive:
        args.append("-recursive")
    if only_active:
        args.append("-active")
    if resolve:
        args.append("-nW")

    result = await _run_command(args, timeout_seconds=timeout + 30)

    if result["return_code"] != 0:
        logger.warning("subfinder command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"subfinder failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"subfinder {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()
    if not stdout:
        return json.dumps({
            "domain": domain,
            "subdomains": [],
            "count": 0,
            "message": "No subdomains found",
        }, indent=2)

    subdomains = []
    raw_entries = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            host = entry.get("host", "")
            if host and host.lower() != domain.lower():
                subdomains.append(host)
            raw_entries.append(entry)
        except json.JSONDecodeError:
            if line and line.lower() != domain.lower():
                subdomains.append(line)

    unique_subdomains = sorted(set(subdomains))

    return json.dumps({
        "domain": domain,
        "subdomains": unique_subdomains,
        "count": len(unique_subdomains),
        "sources_used": list({
            e.get("source", "unknown")
            for e in raw_entries if e.get("source")
        }),
    }, indent=2)


@mcp.tool()
async def run_subfinder(
    arguments: str,
    timeout_seconds: int = 300,
) -> str:
    """Run subfinder with arbitrary command-line arguments.

    Use this for advanced usage or flags not covered by enumerate_subdomains.
    Pass arguments exactly as you would on the command line.

    Args:
        arguments: Command-line arguments string (e.g. "-d example.com -silent").
        timeout_seconds: Maximum execution time in seconds (default 300).
    """
    logger.info("run_subfinder called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("subfinder command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"subfinder failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"subfinder {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()

    if not stdout:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

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


@mcp.tool()
async def list_subfinder_sources() -> str:
    """List all available data sources that subfinder can query.

    Returns the complete list of passive subdomain enumeration sources
    supported by the installed version of subfinder.
    """
    logger.info("list_subfinder_sources called")
    result = await _run_command(["-ls"], timeout_seconds=30)

    if result["return_code"] != 0:
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": "Failed to list sources",
                "detail": error_detail.strip(),
            },
            indent=2,
        )

    stdout = result["stdout"].strip()
    if not stdout:
        return json.dumps({"sources": [], "message": "No sources returned"})

    sources = [line.strip() for line in stdout.splitlines() if line.strip()]
    return json.dumps({"sources": sources, "count": len(sources)}, indent=2)


def main():
    logger.info("Starting subfinder-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
