"""Titus MCP Server - Secret Detection in Source Code via FastMCP."""

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
        path: File or directory path to scan for secrets.
        validate: If True, attempt to validate discovered secrets against live services.
        output_format: Output format - "json" or "csv". Default "json".
        rules_include: Comma-separated rule IDs or tags to include (empty = all rules).
        rules_exclude: Comma-separated rule IDs or tags to exclude.

    Returns:
        Dictionary with scan results including any detected secrets.
    """
    logger.info("scan_path called with path=%s", path)
    args = ["scan", path]

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
        path: Path to a git repository to scan its history.
        validate: If True, attempt to validate discovered secrets against live services.
        output_format: Output format - "json" or "csv". Default "json".
        rules_include: Comma-separated rule IDs or tags to include (empty = all rules).
        rules_exclude: Comma-separated rule IDs or tags to exclude.

    Returns:
        Dictionary with scan results from git history including detected secrets.
    """
    logger.info("scan_git called with path=%s", path)
    args = ["scan", path, "--git"]

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


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8103"))
    logger.info("Starting titus-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
