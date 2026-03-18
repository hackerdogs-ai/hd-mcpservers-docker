#!/usr/bin/env python3
"""Alterx MCP Server — pattern-based wordlist generator for subdomain discovery.

Wraps the alterx CLI (projectdiscovery/alterx) to expose capabilities through
the Model Context Protocol (MCP). Supports stdio and streamable-http (no Minibridge).
"""

import asyncio
import logging
import os
import shutil
import sys
import tempfile

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("alterx-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8380"))

mcp = FastMCP(
    "Alterx MCP Server",
    instructions=(
        "Pattern-based wordlist generator for subdomain discovery using Alterx."
    ),
)

ALTERX_BIN = os.environ.get("ALTERX_BIN", "alterx")


def _find_binary() -> str:
    path = shutil.which(ALTERX_BIN)
    if path is None:
        logger.error("alterx binary not found on PATH")
        raise FileNotFoundError(
            f"alterx not found. Set ALTERX_BIN or ensure it is on PATH."
        )
    return path


async def _run_alterx(
    domain: str,
    pattern: str,
    output_file_path: str | None = None,
    timeout_seconds: int = 120,
) -> dict:
    binary = _find_binary()
    args = ["-l", domain, "-p", pattern]
    if output_file_path:
        args.extend(["-o", output_file_path])

    try:
        proc = await asyncio.create_subprocess_exec(
            binary,
            *args,
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
        return {
            "stdout": "",
            "stderr": f"Command timed out after {timeout_seconds}s",
            "return_code": -1,
        }
    except Exception as exc:
        logger.error("alterx execution failed: %s", exc)
        return {
            "stdout": "",
            "stderr": str(exc),
            "return_code": -1,
        }

    return {
        "stdout": stdout_bytes.decode("utf-8", errors="replace"),
        "stderr": stderr_bytes.decode("utf-8", errors="replace"),
        "return_code": proc.returncode or 0,
    }


@mcp.tool()
async def do_alterx(
    domain: str,
    pattern: str,
    output_file_path: str | None = None,
    timeout_seconds: int = 120,
) -> str:
    """Execute Alterx: generate domain wordlists using pattern-based permutations for subdomain discovery.

    Args:
        domain: Target domain or subdomains (comma-separated or single domain).
        pattern: Pattern template. Examples: "{{word}}-{{sub}}.{{suffix}}", "{{sub}}.{{word}}.{{suffix}}", "{{sub}}{{number}}.{{suffix}}".
        output_file_path: Optional path to save the wordlist (in container). If omitted, output is returned in the response.
        timeout_seconds: Max execution time (default 120).
    """
    logger.info("do_alterx domain=%s pattern=%s", domain, pattern)
    if output_file_path and not os.path.isabs(output_file_path):
        output_file_path = os.path.join(tempfile.gettempdir(), output_file_path)

    result = await _run_alterx(
        domain=domain,
        pattern=pattern,
        output_file_path=output_file_path,
        timeout_seconds=timeout_seconds,
    )

    if result["return_code"] != 0:
        err = result["stderr"] or result["stdout"] or "Unknown error"
        return f"alterx failed (exit {result['return_code']}): {err.strip()}"

    out = result["stdout"].strip()
    if not out:
        return "alterx completed with no output."
    return out + "\nalterx completed successfully"


def main():
    logger.info("Starting alterx-mcp (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
