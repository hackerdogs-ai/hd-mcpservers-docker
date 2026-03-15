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
    instructions=(
        "MCP server for Titus - scans source code, files, and git history for secrets (API keys, tokens, credentials) using 487 detection rules. "
        "Runs in Docker: callers (e.g. AI agents) must pass URLs, not host paths. For scan_path and scan_git, pass a file URL (e.g. https://example.com/archive.zip) or a repo URL (e.g. https://github.com/org/repo); the server downloads the content inside the container and runs the scan. No mounting or local paths required."
    ),
)

TITUS_BIN = shutil.which("titus") or "titus"
# Ensure scan/report use the same datastore (titus.ds in this directory)
TITUS_CWD = os.environ.get("TITUS_CWD", "/app")


def _run_titus(args: list[str], timeout: int = 120) -> dict:
    """Execute titus CLI and return structured result."""
    try:
        result = subprocess.run(
            [TITUS_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=TITUS_CWD,
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


def _path_or_url_ok(path: str) -> tuple[bool, str | None]:
    """Return (True, None) if path is a URL or exists in container; else (False, error_message)."""
    if hd_fetch.is_url(path):
        return True, None
    if os.path.exists(path):
        return True, None
    return (
        False,
        "Path does not exist in the container. This server runs in Docker: pass a URL instead, "
        "e.g. https://github.com/org/repo or https://example.com/archive.zip — the server will download and scan it.",
    )


@mcp.tool()
def scan_path(
    path: str,
    validate: bool = False,
    output_format: str = "json",
    rules_include: str = "",
    rules_exclude: str = "",
) -> dict:
    """Scan files and directories for secrets (API keys, tokens, credentials).

    Designed for Docker and AI agents: pass a URL and the server downloads and scans it.
    Titus uses 487 detection rules on source code, config files, and text files.

    Args:
        path: URL to scan (recommended). HTTP(S) file or archive URL, or GitHub/GitLab repo URL
              (e.g. https://github.com/org/repo, https://example.com/code.zip). The server downloads
              the content inside the container and runs the scan. Alternatively, a path inside the
              container (e.g. from download_file) if content was already downloaded.
        validate: If True, validate discovered secrets against live services.
        output_format: "json" or "csv". Default "json".
        rules_include: Comma-separated rule IDs or tags to include (empty = all).
        rules_exclude: Comma-separated rule IDs or tags to exclude.

    Returns:
        Dict with success, output (scan results/findings), stderr, exit_code.
    """
    logger.info("scan_path called with path=%s", path)

    ok, err = _path_or_url_ok(path)
    if not ok:
        logger.warning("scan_path rejected path (not URL and not in container): %s", path)
        return {"success": False, "output": None, "stderr": err, "exit_code": -1}

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

    Designed for Docker and AI agents: pass a repo URL and the server clones and scans history.
    Examines every commit to find secrets that were committed and later removed.

    Args:
        path: URL to a git repository (recommended). GitHub/GitLab URL (e.g. https://github.com/org/repo).
              The server clones the repo inside the container and scans full git history.
              Alternatively, a path inside the container (e.g. from download_file) if already cloned.
        validate: If True, validate discovered secrets against live services.
        output_format: "json" or "csv". Default "json".
        rules_include: Comma-separated rule IDs or tags to include (empty = all).
        rules_exclude: Comma-separated rule IDs or tags to exclude.

    Returns:
        Dict with success, output (findings from git history), stderr, exit_code.
    """
    logger.info("scan_git called with path=%s", path)

    ok, err = _path_or_url_ok(path)
    if not ok:
        logger.warning("scan_git rejected path (not URL and not in container): %s", path)
        return {"success": False, "output": None, "stderr": err, "exit_code": -1}

    with hd_fetch.resolve(path) as local_path:
        args = ["scan", "--git", local_path]

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

    Returns the full set of 487 built-in detection rules that Titus uses to
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

    Use when you need to download once and run multiple scans (scan_path, scan_git) on the same
    content, or to inspect the path before scanning. For a single scan, passing the URL directly
    to scan_path or scan_git is simpler; they download and scan in one step.

    Args:
        url: Any HTTP(S) file URL, GitHub/GitLab repo URL (e.g. https://github.com/org/repo), or data: URI.
        extract: If True (default), automatically extract archives (.zip, .tar.gz, etc.).

    Returns:
        Dict with 'path' (use this path in scan_path/scan_git) and 'job_id' (pass to cleanup_downloads when done).
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
