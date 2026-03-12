#!/usr/bin/env python3
"""OWASP ZAP MCP Server — Automated security scanning proxy (headless).

Wraps the zap.sh CLI (zaproxy/zap-core) to expose
capabilities through the Model Context Protocol (MCP).
"""

import asyncio
import json
import logging
import os
import shutil
import sys
import tempfile
import uuid

from fastmcp import FastMCP

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("zap-mcp")

MCP_TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio")
MCP_PORT = int(os.environ.get("MCP_PORT", "8231"))

mcp = FastMCP(
    "OWASP ZAP MCP Server",
    instructions=(
        "Automated security scanning proxy (headless)."
    ),
)

ZAP_BIN = os.environ.get("ZAP_BIN", "zap.sh")


def _find_binary() -> str:
    """Locate the zap.sh binary, raising a clear error if missing."""
    path = shutil.which(ZAP_BIN)
    if path is None:
        logger.error("zap.sh binary not found on PATH")
        raise FileNotFoundError(
            f"zap.sh binary not found. Ensure it is installed and available "
            f"on PATH, or set ZAP_BIN to the full path."
        )
    return path


async def _run_command(args: list[str], timeout_seconds: int = 600) -> dict:
    """Execute a zap.sh command and return structured output.

    Returns a dict with keys: stdout, stderr, return_code.
    Uses a unique HOME per run so ZAP does not hit "another instance is locking" in the same container.
    """
    binary = _find_binary()
    cmd = [binary] + args

    # Unique ZAP home per invocation to avoid "another ZAP instance is already running" lock
    zap_home = os.path.join(tempfile.gettempdir(), f"zap-run-{uuid.uuid4().hex[:12]}")
    os.makedirs(zap_home, exist_ok=True)
    env = os.environ.copy()
    env["HOME"] = zap_home

    try:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
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
    finally:
        try:
            shutil.rmtree(zap_home, ignore_errors=True)
        except Exception:
            pass


@mcp.tool()
async def run_zap(
    arguments: str,
    timeout_seconds: int = 600,
) -> str:
    """Run zap.sh with the given arguments.

    Pass arguments as you would on the command line.

    Args:
        arguments: Command-line arguments string.
        timeout_seconds: Maximum execution time in seconds (default 600).
    """
    import shlex

    logger.info("run_zap called with arguments=%s", arguments)
    args = shlex.split(arguments) if arguments.strip() else []
    # Help/version only: do not add -daemon so ZAP prints and exits quickly (avoids timeout)
    help_version = {"-help", "--help", "-h", "-version", "--version", "-v"}
    if args and set(a.strip().lower() for a in args) <= help_version:
        pass  # run as-is: zap.sh -help exits with output
    else:
        # Force daemon/headless when no mode flag (avoids "ZAP GUI is not supported on a headless environment")
        mode_flags = {"-daemon", "-cmd", "-quickurl", "-script", "-regression"}
        has_mode = any(a in mode_flags or a.lstrip("-").startswith("daemon") for a in args)
        if not has_mode:
            args = ["-daemon"] + args
    result = await _run_command(args, timeout_seconds=timeout_seconds)

    if result["return_code"] != 0:
        logger.warning("zap.sh command failed with exit code %d", result["return_code"])
        error_detail = result["stderr"] or result["stdout"] or "Unknown error"
        return json.dumps(
            {
                "error": True,
                "message": f"zap.sh failed (exit code {result['return_code']})",
                "detail": error_detail.strip(),
                "command": f"zap.sh {' '.join(args)}",
            },
            indent=2,
        )

    stdout = result["stdout"].strip()
    stderr = result["stderr"].strip()

    # Many CLI tools (including zap.sh) send help/version to stderr; always include both so output is visible
    if not stdout and stderr:
        return json.dumps(
            {
                "message": "Output (from stderr):",
                "stdout": "",
                "stderr": stderr,
                "arguments": arguments,
            },
            indent=2,
        )
    if not stdout and not stderr:
        return json.dumps({"message": "Command completed with no output", "arguments": arguments})
    if stderr:
        # Success but we have both stdout and stderr (e.g. help on stderr, other on stdout)
        return json.dumps(
            {
                "stdout": stdout,
                "stderr": stderr,
                "arguments": arguments,
            },
            indent=2,
        )

    # Try to parse as JSON/JSONL
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


def main():
    logger.info("Starting zap-mcp server (transport=%s, port=%s)", MCP_TRANSPORT, MCP_PORT)
    if MCP_TRANSPORT == "stdio":
        mcp.run(transport="stdio", show_banner=False)
    else:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)


if __name__ == "__main__":
    main()
