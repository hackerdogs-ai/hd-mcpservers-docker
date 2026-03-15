#!/usr/bin/env python3
"""OnionSearch MCP Server — Dark Web .onion search engine scraper.

Wraps the OnionSearch CLI (megadose/OnionSearch) to expose Dark Web search
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import csv
import io
import json
import logging
import os
import shlex
import shutil
import sys
import tempfile

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("onionsearch-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8372"))

mcp = FastMCP(
    "OnionSearch MCP Server",
    instructions=(
        "Dark Web .onion search engine scraper. Searches across multiple Tor "
        "hidden service search engines. Requires a Tor SOCKS5 proxy (TOR_PROXY env var)."
    ),
)

BIN_NAME = os.environ.get("ONIONSEARCH_BIN", "onionsearch")


def _find_binary() -> str:
    """Locate the onionsearch binary, raising a clear error if missing."""
    if os.path.isabs(BIN_NAME) and os.path.isfile(BIN_NAME):
        return BIN_NAME
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error("onionsearch binary not found on PATH")
        raise FileNotFoundError(
            f"onionsearch binary not found. Ensure it is installed and available "
            f"on PATH, or set ONIONSEARCH_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 300) -> dict:
    """Execute an onionsearch command and return structured output."""
    cmd = [_find_binary()] + args

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
            "stderr": f"Command timed out after {timeout_seconds}s",
            "return_code": -1,
        }
    except Exception as exc:
        logger.error("Command execution failed: %s", exc)
        return {
            "stdout": "",
            "stderr": f"Failed to execute command: {exc}",
            "return_code": -1,
        }

    return {
        "stdout": stdout_bytes.decode("utf-8", errors="replace"),
        "stderr": stderr_bytes.decode("utf-8", errors="replace"),
        "return_code": proc.returncode,
    }


@mcp.tool()
async def run_onionsearch(
    arguments: str,
    timeout_seconds: int = 300,
) -> str:
    """Run onionsearch with the given arguments.

    Pass arguments as you would on the command line. OnionSearch scrapes
    .onion search engines via Tor to find Dark Web URLs.

    The TOR_PROXY environment variable is automatically injected as --proxy
    unless you explicitly include --proxy in your arguments.

    Args:
        arguments: Command-line arguments string (e.g. '"search term" --limit 3').
        timeout_seconds: Maximum execution time in seconds (default 300).
    """
    logger.info("run_onionsearch called with arguments=%s", arguments)

    args = shlex.split(arguments) if arguments.strip() else []

    tor_proxy = os.environ.get("TOR_PROXY", "127.0.0.1:9050")
    if "--proxy" not in arguments:
        args.extend(["--proxy", tor_proxy])

    result = await _run_command(args, timeout_seconds=timeout_seconds)

    output = result["stdout"].strip()
    stderr = result["stderr"].strip()

    if result["return_code"] != 0 and not output:
        error_detail = stderr or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"onionsearch exited with code {result['return_code']}",
                "detail": error_detail,
            },
            indent=2,
        )

    combined = output
    if stderr:
        combined = f"{output}\n\n--- stderr ---\n{stderr}" if output else stderr

    if not combined:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})

    return combined


@mcp.tool()
async def onionsearch_search(
    query: str,
    engines: str = "",
    exclude: str = "",
    limit: int = 3,
    timeout_seconds: int = 300,
) -> str:
    """Search Dark Web .onion search engines for a query term.

    Higher-level tool that builds the OnionSearch command for you.
    Returns CSV-formatted results (engine, name, url).

    Args:
        query: Search query string (required).
        engines: Space-separated engine names to search (e.g. "ahmia tor66 phobos").
                 If empty, searches all available engines.
        exclude: Space-separated engine names to exclude (e.g. "notevil candle").
        limit: Maximum pages per engine to scrape (default 3).
        timeout_seconds: Maximum execution time in seconds (default 300).
    """
    logger.info("onionsearch_search called query=%s engines=%s limit=%d", query, engines, limit)

    args = [query]

    tor_proxy = os.environ.get("TOR_PROXY", "127.0.0.1:9050")
    args.extend(["--proxy", tor_proxy])

    args.extend(["--limit", str(limit)])

    output_file = tempfile.mktemp(prefix="onionsearch_", suffix=".csv", dir="/tmp")
    args.extend(["--output", output_file])

    if engines.strip():
        args.extend(["--engines"] + engines.strip().split())

    if exclude.strip():
        args.extend(["--exclude"] + exclude.strip().split())

    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        stderr = result["stderr"].strip()
        return json.dumps(
            {
                "error": True,
                "message": f"OnionSearch failed (exit code {result['return_code']})",
                "detail": stderr or result["stdout"].strip() or "Unknown error",
            },
            indent=2,
        )

    csv_content = ""
    try:
        with open(output_file, "r") as f:
            csv_content = f.read().strip()
    except FileNotFoundError:
        pass
    finally:
        try:
            os.unlink(output_file)
        except OSError:
            pass

    if not csv_content:
        return json.dumps({
            "query": query,
            "results": [],
            "message": "No results found. Search engines may be unavailable or query returned no matches.",
            "stderr": result["stderr"].strip()[:500] if result["stderr"] else "",
        }, indent=2)

    results = []
    try:
        reader = csv.reader(io.StringIO(csv_content))
        for row in reader:
            if len(row) >= 3:
                results.append({
                    "engine": row[0],
                    "name": row[1],
                    "url": row[2],
                })
            elif len(row) == 2:
                results.append({"engine": row[0], "name": "", "url": row[1]})
    except Exception as e:
        logger.warning("CSV parse error: %s", e)
        return csv_content

    return json.dumps({
        "query": query,
        "results_count": len(results),
        "results": results,
    }, indent=2)


def main():
    logger.info("Starting onionsearch-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
