#!/usr/bin/env python3
"""Suricata MCP Server — network intrusion detection and prevention.

Wraps the Suricata IDS/IPS binary to expose network traffic analysis
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shlex
import shutil
import sys
import tempfile

from fastmcp import FastMCP
import hd_fetch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("suricata-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8365"))

mcp = FastMCP(
    "Suricata MCP Server",
    instructions=(
        "Suricata network intrusion detection and prevention system. "
        "Analyze PCAP files, inspect rules, and detect threats."
    ),
)

BIN_NAME = os.environ.get("SURICATA_BIN", "suricata")


def _find_binary() -> str:
    """Locate the suricata binary, raising a clear error if missing."""
    if os.path.isabs(BIN_NAME) and os.path.isfile(BIN_NAME):
        return BIN_NAME
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error("suricata binary not found on PATH")
        raise FileNotFoundError(
            f"suricata binary not found. Ensure it is installed and available "
            f"on PATH, or set SURICATA_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a suricata command and return structured output."""
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
async def run_suricata(
    arguments: str,
    source_url: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Run suricata with the given arguments.

    Pass arguments as you would on the command line. Use ``source_url`` to
    have the server download PCAP files from a URL before processing.

    Args:
        arguments: Command-line arguments string (e.g. "-V" or "-r /path/to/file.pcap -l /app/output").
                   Use ``{source}`` as a placeholder for the downloaded file path when using *source_url*.
        source_url: Optional HTTP(S) URL or GitHub repo URL. Downloaded into the container;
                    local path replaces ``{source}`` in *arguments* or is appended.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("run_suricata called with arguments=%s source_url=%s", arguments, source_url)

    job_info = None
    try:
        if source_url:
            try:
                job_info = hd_fetch.fetch(source_url)
            except hd_fetch.FetchError as exc:
                return json.dumps({"error": True, "message": str(exc)}, indent=2)
            if "{source}" in arguments:
                arguments = arguments.replace("{source}", job_info["path"])
            else:
                arguments = f"{arguments} {job_info['path']}".strip()

        args = shlex.split(arguments) if arguments.strip() else []
        result = await _run_command(args, timeout_seconds=timeout_seconds)

        output = result["stdout"].strip()
        stderr = result["stderr"].strip()

        if result["return_code"] != 0 and not output:
            error_detail = stderr or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"suricata exited with code {result['return_code']}",
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
    finally:
        if job_info:
            hd_fetch.cleanup(job_info["job_id"])


@mcp.tool()
async def analyze_pcap(
    pcap_path: str = "",
    source_url: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Analyze a PCAP file with Suricata and return alerts.

    Runs Suricata against a PCAP file and returns the alerts (fast.log)
    and EVE JSON log if generated.

    Args:
        pcap_path: Path to a PCAP file already in the container.
        source_url: HTTP(S) URL to download the PCAP from. If both pcap_path and
                    source_url are provided, source_url takes precedence.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    logger.info("analyze_pcap called pcap_path=%s source_url=%s", pcap_path, source_url)

    job_info = None
    out_dir = tempfile.mkdtemp(prefix="suricata-", dir="/app/output")

    try:
        target = pcap_path
        if source_url:
            try:
                job_info = hd_fetch.fetch(source_url)
                target = job_info["path"]
            except hd_fetch.FetchError as exc:
                return json.dumps({"error": True, "message": str(exc)}, indent=2)

        if not target:
            return json.dumps({"error": True, "message": "Provide pcap_path or source_url"})

        result = await _run_command(
            ["-r", target, "-l", out_dir, "--set", "outputs.0.fast.enabled=yes"],
            timeout_seconds=timeout_seconds,
        )

        response = {
            "return_code": result["return_code"],
            "stderr_summary": result["stderr"].strip()[:500] if result["stderr"] else "",
        }

        fast_log = os.path.join(out_dir, "fast.log")
        if os.path.isfile(fast_log):
            with open(fast_log, "r") as f:
                alerts = f.read().strip()
            response["alerts"] = alerts if alerts else "No alerts generated."
        else:
            response["alerts"] = "No fast.log generated — check if rules are loaded."

        eve_json = os.path.join(out_dir, "eve.json")
        if os.path.isfile(eve_json):
            events = []
            with open(eve_json, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            if events:
                response["eve_events_count"] = len(events)
                alert_events = [e for e in events if e.get("event_type") == "alert"]
                if alert_events:
                    response["alert_events"] = alert_events[:50]

        return json.dumps(response, indent=2, default=str)
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)
        if job_info:
            hd_fetch.cleanup(job_info["job_id"])


@mcp.tool()
async def download_file(
    url: str,
    extract: bool = True,
) -> str:
    """Download a file or repository from a URL into the container workspace.

    Use this to pre-download PCAP files before analysis, or when you need to
    download once and run multiple analyses on the same content.

    Args:
        url: HTTP(S) URL, GitHub/GitLab repo URL, or data: URI.
        extract: If True (default), automatically extract archives (.zip, .tar.gz, etc.).

    Returns:
        JSON with 'path' (local path to use in other tools) and
        'job_id' (use with cleanup_downloads to free space).
    """
    try:
        info = hd_fetch.fetch(url, extract=extract)
        return json.dumps(info, indent=2)
    except hd_fetch.FetchError as exc:
        return json.dumps({"error": True, "message": str(exc)}, indent=2)


@mcp.tool()
async def cleanup_downloads(job_id: str = "") -> str:
    """Clean up downloaded files from the container workspace.

    Args:
        job_id: Specific job ID to clean up. If empty, removes all downloads.

    Returns:
        JSON confirming the cleanup.
    """
    if job_id:
        hd_fetch.cleanup(job_id)
        return json.dumps({"cleaned": job_id})
    hd_fetch.cleanup_all()
    return json.dumps({"cleaned": "all"})


def main():
    logger.info("Starting suricata-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
