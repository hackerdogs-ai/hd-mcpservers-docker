#!/usr/bin/env python3
"""Binwalk MCP Server — Firmware analysis and extraction.

Wraps the binwalk CLI (ReFirmLabs/binwalk) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shutil
import sys

from fastmcp import FastMCP
import hd_fetch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("binwalk-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8241"))

mcp = FastMCP(
    "Binwalk MCP Server",
    instructions=(
        "Firmware analysis and extraction."
    ),
)

BINWALK_BIN = os.environ.get("BINWALK_BIN", "binwalk")


def _find_binary() -> str:
    """Locate the binwalk binary, raising a clear error if missing."""
    path = shutil.which(BINWALK_BIN)
    if path is None:
        logger.error("binwalk binary not found on PATH")
        raise FileNotFoundError(
            f"binwalk binary not found. Ensure it is installed and available "
            f"on PATH, or set BINWALK_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a binwalk command and return structured output.

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
async def run_binwalk(
    arguments: str,
    source_url: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run binwalk with the given arguments.

    Pass arguments as you would on the command line.  Use ``source_url`` to
    have the server download a firmware image or binary from a URL before
    analysis.

    Args:
        arguments: Command-line arguments string.  Use ``{source}`` as a
                   placeholder for the downloaded file path when using
                   *source_url*.
        source_url: Optional HTTP(S) URL to a firmware image, binary, or
                    archive.  The file is downloaded into the container and
                    its local path replaces any ``{source}`` placeholder in
                    *arguments*, or is appended if no placeholder is present.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_binwalk called with arguments=%s source_url=%s", arguments, source_url)

    job_info = None
    try:
        if source_url:
            try:
                job_info = hd_fetch.fetch(source_url, extract=False)
            except hd_fetch.FetchError as exc:
                return json.dumps({"error": True, "message": str(exc)}, indent=2)
            if "{source}" in arguments:
                arguments = arguments.replace("{source}", job_info["path"])
            else:
                arguments = f"{arguments} {job_info['path']}".strip()

        args = shlex.split(arguments) if arguments.strip() else []
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        if result["return_code"] != 0:
            logger.warning("binwalk command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"binwalk failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"binwalk {' '.join(args)}",
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
    finally:
        if job_info:
            hd_fetch.cleanup(job_info["job_id"])


@mcp.tool()
async def download_file(
    url: str,
    extract: bool = True,
) -> str:
    """Download a file from a URL into the container workspace.

    Use this to pre-download firmware or binaries before running analysis,
    or when you need to download once and run multiple analyses on the same file.

    Args:
        url: HTTP(S) URL or data: URI pointing to a firmware image or binary.
        extract: If True (default), automatically extract archives (.zip, .tar.gz, etc.).
                 Set to False for raw binary files you want to analyze directly.

    Returns:
        JSON with 'path' (local path to use in other tools) and
        'job_id' (use with cleanup_downloads to free space).
    """
    logger.info("download_file called with url=%s", url)
    try:
        info = hd_fetch.fetch(url, extract=extract)
        return json.dumps(info, indent=2)
    except hd_fetch.FetchError as exc:
        return json.dumps({"error": True, "message": str(exc)}, indent=2)


@mcp.tool()
async def cleanup_downloads(job_id: str = "") -> str:
    """Clean up downloaded files from the container workspace.

    Args:
        job_id: Specific job ID to clean up.  If empty, removes all downloads.

    Returns:
        JSON confirming the cleanup.
    """
    if job_id:
        hd_fetch.cleanup(job_id)
        return json.dumps({"cleaned": job_id})
    hd_fetch.cleanup_all()
    return json.dumps({"cleaned": "all"})


def main():
    logger.info("Starting binwalk-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
