#!/usr/bin/env python3
"""Gitleaks MCP Server — Secret detection tool for git repositories and files.

Wraps the gitleaks CLI (gitleaks/gitleaks) to expose
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
logger = logging.getLogger("gitleaks-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8332"))

mcp = FastMCP(
    "Gitleaks MCP Server",
    instructions=(
        "Secret detection tool for git repositories and files."
    ),
)

BIN_NAME = os.environ.get("GITLEAKS_BIN", "gitleaks")


def _find_binary() -> str:
    """Locate the gitleaks binary, raising a clear error if missing."""
    path = shutil.which(BIN_NAME)
    if path is None:
        logger.error("gitleaks binary not found on PATH")
        raise FileNotFoundError(
            f"gitleaks binary not found. Ensure it is installed and available "
            f"on PATH, or set GITLEAKS_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a gitleaks command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    """
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


@mcp.tool()
async def run_gitleaks(
    arguments: str = "",
    source_url: str = "",
    timeout_seconds: int = 600,
) -> str:
    """Scan a git repository or directory for hardcoded secrets using gitleaks.

    When source_url is provided, the repository is cloned automatically and
    scanned with ``gitleaks git <path>``.  You usually only need source_url.

    Examples:
        Scan a GitHub repo:  source_url="https://github.com/org/repo"
        Scan with verbose:   source_url="https://github.com/org/repo", arguments="--verbose"

    Args:
        arguments: Extra CLI flags (e.g. ``--verbose``, ``--config /path``).
                   Do NOT pass the subcommand (git/dir) or the path — those
                   are added automatically when source_url is set.
        source_url: GitHub/GitLab repo URL, HTTP(S) file URL, or archive URL.
                    The server clones/downloads it and scans automatically.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_gitleaks called with arguments=%s source_url=%s", arguments, source_url)

    job_info = None
    try:
        if source_url:
            try:
                job_info = hd_fetch.fetch(source_url)
            except hd_fetch.FetchError as exc:
                return json.dumps({"error": True, "message": str(exc)}, indent=2)

        extra = shlex.split(arguments) if arguments.strip() else []

        # Strip bogus flags the LLM sometimes generates.
        extra = [a for a in extra if not a.startswith("--source")]

        if job_info:
            local_path = job_info["path"]
            # Pick the right subcommand based on what was downloaded.
            has_subcommand = any(a in extra for a in ("git", "dir", "stdin"))
            if not has_subcommand:
                is_git = os.path.isdir(os.path.join(local_path, ".git"))
                subcommand = "git" if is_git else "dir"
                args = [subcommand, local_path] + extra
            else:
                # User explicitly set a subcommand; append path.
                args = extra + [local_path]
        elif "{source}" in arguments:
            args = extra
        else:
            args = extra

        # Default to JSON report output so findings are machine-readable.
        if not any(a.startswith("--report-format") or a.startswith("-f") for a in args):
            args.extend(["--report-format", "json"])
        if not any(a.startswith("--report-path") or a.startswith("-r") for a in args):
            args.extend(["--report-path", "/tmp/gitleaks-report.json"])

        result = await _run_command(args, timeout_seconds=timeout_seconds)

        # gitleaks exit codes: 0 = no leaks, 1 = leaks found, >1 = error.
        if result["return_code"] not in (0, 1):
            logger.warning("gitleaks command failed with exit code %d", result["return_code"])
            error_detail = result["stderr"] or result["stdout"] or "Unknown error"
            return json.dumps(
                {
                    "error": True,
                    "message": f"gitleaks failed (exit code {result['return_code']})",
                    "detail": error_detail.strip(),
                    "command": f"gitleaks {' '.join(args)}",
                },
                indent=2,
            )

        # Try to read the JSON report file first (structured findings).
        report_findings = []
        try:
            with open("/tmp/gitleaks-report.json", "r") as f:
                report_findings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

        if report_findings:
            return json.dumps(
                {
                    "leaks_found": len(report_findings),
                    "exit_code": result["return_code"],
                    "findings": report_findings,
                    "summary": result["stderr"].strip() if result["stderr"] else "",
                },
                indent=2,
            )

        # Fallback to stdout parsing.
        stdout = result["stdout"].strip()

        if not stdout and result["return_code"] == 0:
            return json.dumps({"leaks_found": 0, "message": "No leaks detected"})

        if not stdout:
            return json.dumps({
                "leaks_found": 0,
                "message": "Scan completed",
                "summary": result["stderr"].strip() if result["stderr"] else "",
            })

        results = []
        for line in stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                results.append({"raw": line})

        return json.dumps(
            {
                "leaks_found": len(results),
                "exit_code": result["return_code"],
                "findings": results,
                "summary": result["stderr"].strip() if result["stderr"] else "",
            },
            indent=2,
        )
    finally:
        if job_info:
            hd_fetch.cleanup(job_info["job_id"])



@mcp.tool()
async def download_file(
    url: str,
    extract: bool = True,
) -> str:
    """Download a file or repository from a URL into the container workspace.

    Use this to pre-download files before analysis, or when you need to
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
    logger.info("Starting gitleaks-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
