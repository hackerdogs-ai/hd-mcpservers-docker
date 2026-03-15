"""Nerva MCP Server - Network Service Fingerprinting via FastMCP."""

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
logger = logging.getLogger("nerva-mcp")

mcp = FastMCP(
    "nerva-mcp",
    instructions=(
        "MCP server for Nerva - identifies 120+ network services on open ports and extracts version/config metadata. "
        "Runs in Docker. Output is JSON by default. Callers (e.g. AI agents) pass comma-separated host:port targets (e.g. example.com:80,10.0.0.1:443); targets must be reachable from the container network."
    ),
)

NERVA_BIN = shutil.which("nerva") or "nerva"
NERVA_CWD = os.environ.get("NERVA_CWD", "/app")


def _run_nerva(args: list[str], timeout: int = 120) -> dict:
    """Execute nerva CLI and return structured result."""
    try:
        result = subprocess.run(
            [NERVA_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=NERVA_CWD,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("nerva exited with code %d: %s", result.returncode, stderr)

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
        logger.error("nerva binary not found at '%s'", NERVA_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"nerva binary not found at '{NERVA_BIN}'. Ensure nerva is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("nerva command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"nerva command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("nerva command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def fingerprint_services(
    targets: str,
    output_format: str = "json",
    fast_mode: bool = False,
    udp: bool = False,
    timeout: int = 2000,
) -> dict:
    """Identify network services running on open ports and extract version/config metadata.

    Output is JSON by default. Nerva probes host:port targets to fingerprint 120+ service types
    (HTTP servers, databases, message queues, caches, etc.).

    Args:
        targets: Comma-separated host:port pairs (e.g. "example.com:80,10.0.0.1:443"). Must be reachable from the container.
        output_format: "json" (default) or "csv". Default is always JSON when not specified.
        fast_mode: If True, use fast mode (default ports only).
        udp: If True, also probe UDP ports.
        timeout: Connection timeout in milliseconds. Default 2000.

    Returns:
        Dict with success, output (JSON array of fingerprint results or parsed JSON), stderr, exit_code.
    """
    logger.info("fingerprint_services called with targets=%s", targets)
    target_list = [t.strip() for t in targets.split(",") if t.strip()]

    if not target_list:
        return {
            "success": False,
            "output": None,
            "stderr": "No targets provided. Pass comma-separated host:port pairs (e.g. example.com:80,10.0.0.1:443).",
            "exit_code": -1,
        }

    args = ["-t", ",".join(target_list)]

    # Default output is JSON; only use CSV when explicitly requested
    if (output_format or "").strip().lower() == "csv":
        args.append("--csv")
    else:
        args.append("--json")

    if fast_mode:
        args.append("--fast")

    if udp:
        args.append("--udp")

    args.extend(["-w", str(timeout)])

    overall_timeout = max((timeout / 1000) * len(target_list) * 2, 30) + 30
    return _run_nerva(args, timeout=int(overall_timeout))


@mcp.tool()
def list_capabilities() -> dict:
    """List all supported service detection plugins.

    Returns the set of 120+ service types that Nerva can identify, including
    plugin names and the protocols/services they detect.

    Returns:
        Dictionary with available service detection plugins.
    """
    logger.info("list_capabilities called")
    return _run_nerva(["-c"])


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8104"))
    logger.info("Starting nerva-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
