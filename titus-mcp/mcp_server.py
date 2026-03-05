"""Titus MCP Server - Secret Detection in Source Code via FastMCP."""

import json
import os
import subprocess
import shutil
import sys
import logging

from fastmcp import FastMCP
import hd_fetch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("titus-mcp")

mcp = FastMCP(
    "titus-mcp",
    instructions="MCP server for Titus - scans source code, files, and git history for secrets (API keys, tokens, credentials) using 459 detection rules.",
)

TITUS_BIN = shutil.which("titus") or "titus"


def _run_titus(args: list[str], timeout: int = 120) -> dict:
    """Execute titus CLI and return structured result."""
    try:
        result = subprocess.run(
            [TITUS_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("titus exited with code %d: %s", result.returncode, stderr)

        parsed = None
        if output:
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                lines = output.splitlines()
                json_results = []
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
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
        logger.error("titus binary not found at '%s'", TITUS_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"titus binary not found at '{TITUS_BIN}'. Ensure titus is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("titus command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"titus command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("titus command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def scan_path(
    path: str,
    validate: bool = False,
    output_format: str = "json",
    rules_include: str = "",
    rules_exclude: str = "",
) -> dict:
    """Scan files and directories for secrets such as API keys, tokens, and credentials.

    Titus uses 459 detection rules to find hardcoded secrets in source code,
    configuration files, and other text-based files.

    Args:
        path: Local path OR URL to scan.  Accepts a file/directory path, an
              HTTP(S) URL to a file or archive, or a GitHub/GitLab repo URL.
              URLs are downloaded into the container automatically.
        validate: If True, attempt to validate discovered secrets against live services.
        output_format: Output format - "json" or "csv". Default "json".
        rules_include: Comma-separated rule IDs or tags to include (empty = all rules).
        rules_exclude: Comma-separated rule IDs or tags to exclude.

    Returns:
        Dictionary with scan results including any detected secrets.
    """
    logger.info("scan_path called with path=%s", path)

    with hd_fetch.resolve(path) as local_path:
        args = ["scan", local_path]

        if validate:
            args.append("--validate")

        if output_format:
            args.extend(["--format", output_format])

        if rules_include:
            args.extend(["--rules-include", rules_include])

        if rules_exclude:
            args.extend(["--rules-exclude", rules_exclude])

        return _run_titus(args, timeout=300)


@mcp.tool()
def scan_git(
    path: str,
    validate: bool = False,
    output_format: str = "json",
    rules_include: str = "",
    rules_exclude: str = "",
) -> dict:
    """Scan git history of a repository for secrets leaked in past commits.

    Examines every commit in the git log to find secrets that may have been
    committed and later removed but still exist in history.

    Args:
        path: Local path OR URL to a git repository.  Accepts a directory path
              or a GitHub/GitLab repo URL (e.g. https://github.com/org/repo).
              URLs are cloned into the container automatically.
        validate: If True, attempt to validate discovered secrets against live services.
        output_format: Output format - "json" or "csv". Default "json".
        rules_include: Comma-separated rule IDs or tags to include (empty = all rules).
        rules_exclude: Comma-separated rule IDs or tags to exclude.

    Returns:
        Dictionary with scan results from git history including detected secrets.
    """
    logger.info("scan_git called with path=%s", path)

    with hd_fetch.resolve(path) as local_path:
        args = ["scan", local_path, "--git"]

        if validate:
            args.append("--validate")

        if output_format:
            args.extend(["--format", output_format])

        if rules_include:
            args.extend(["--rules-include", rules_include])

        if rules_exclude:
            args.extend(["--rules-exclude", rules_exclude])

        return _run_titus(args, timeout=600)


@mcp.tool()
def list_rules() -> dict:
    """List all available secret detection rules.

    Returns the full set of 459 built-in detection rules that Titus uses to
    identify secrets, including rule IDs, descriptions, and patterns.

    Returns:
        Dictionary with all available detection rules.
    """
    logger.info("list_rules called")
    return _run_titus(["rules", "list"])


@mcp.tool()
def generate_report(
    output_format: str = "json",
) -> dict:
    """Generate a report of findings from the most recent scan.

    Produces a summary report of all secrets found during the last scan session.

    Args:
        output_format: Output format - "json" or "csv". Default "json".

    Returns:
        Dictionary with the report of scan findings.
    """
    logger.info("generate_report called with output_format=%s", output_format)
    args = ["report"]

    if output_format:
        args.extend(["--format", output_format])

    return _run_titus(args)


@mcp.tool()
def download_file(
    url: str,
    extract: bool = True,
) -> dict:
    """Download a file or repository from a URL into the container workspace.

    Use this to pre-download files before scanning, or when you need to
    download once and run multiple scans on the same content.

    Args:
        url: HTTP(S) URL, GitHub/GitLab repo URL, or data: URI.
        extract: If True (default), automatically extract archives (.zip, .tar.gz, etc.).

    Returns:
        Dictionary with 'path' (local path to use in other tools) and
        'job_id' (use with cleanup_downloads to free space).
    """
    logger.info("download_file called with url=%s", url)
    try:
        return hd_fetch.fetch(url, extract=extract)
    except hd_fetch.FetchError as exc:
        return {"error": True, "message": str(exc)}


@mcp.tool()
def cleanup_downloads(job_id: str = "") -> dict:
    """Clean up downloaded files from the container workspace.

    Args:
        job_id: Specific job ID to clean up.  If empty, removes all downloads.

    Returns:
        Dictionary confirming the cleanup.
    """
    if job_id:
        hd_fetch.cleanup(job_id)
        return {"cleaned": job_id}
    hd_fetch.cleanup_all()
    return {"cleaned": "all"}


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8103"))
    logger.info("Starting titus-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
