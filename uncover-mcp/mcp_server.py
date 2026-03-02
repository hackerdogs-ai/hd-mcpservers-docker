"""Uncover MCP Server - Exposed Host Discovery via FastMCP."""

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
logger = logging.getLogger("uncover-mcp")

mcp = FastMCP(
    "uncover-mcp",
    instructions="MCP server for Uncover - discovers exposed hosts via search APIs (Shodan, Censys, FOFA, Hunter, Quake, etc.).",
)

UNCOVER_BIN = shutil.which("uncover") or "uncover"

SUPPORTED_ENGINE_KEYS = {
    "shodan": "SHODAN_API_KEY",
    "censys": "CENSYS_API_TOKEN",
    "fofa": "FOFA_EMAIL",
    "quake": "QUAKE_TOKEN",
    "hunter": "HUNTER_API_KEY",
    "zoomeye": "ZOOMEYE_API_KEY",
    "netlas": "NETLAS_API_KEY",
    "criminalip": "CRIMINALIP_API_KEY",
    "publicwww": "PUBLICWWW_API_KEY",
    "hunterhow": "HUNTERHOW_API_KEY",
    "google": "GOOGLE_API_KEY",
    "onyphe": "ONYPHE_API_KEY",
    "driftnet": "DRIFTNET_API_KEY",
}


def _check_engine_keys(engines: str) -> str | None:
    """Return a warning if required API keys are missing for the selected engines."""
    missing = []
    for engine in engines.split(","):
        engine = engine.strip().lower()
        if engine == "shodan-idb":
            continue
        env_var = SUPPORTED_ENGINE_KEYS.get(engine)
        if env_var and not os.environ.get(env_var):
            missing.append(f"{engine} ({env_var})")
    if missing:
        return (
            f"Missing API keys for engines: {', '.join(missing)}. "
            "Set the corresponding environment variables or use 'shodan-idb' (no key required). "
            "See https://github.com/projectdiscovery/uncover#provider-configuration"
        )
    return None


def _run_uncover(args: list[str], stdin_data: str | None = None, timeout: int = 120) -> dict:
    """Execute uncover CLI and return structured result."""
    try:
        if stdin_data:
            result = subprocess.run(
                [UNCOVER_BIN] + args,
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            result = subprocess.run(
                [UNCOVER_BIN] + args,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("uncover exited with code %d: %s", result.returncode, stderr)

        parsed = None
        if output:
            lines = output.splitlines()
            json_results = []
            for line in lines:
                try:
                    json_results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            if json_results:
                parsed = json_results
            elif not json_results:
                try:
                    parsed = json.loads(output)
                except json.JSONDecodeError:
                    pass

        return {
            "success": result.returncode == 0,
            "output": parsed if parsed is not None else output,
            "stderr": stderr if stderr else None,
            "exit_code": result.returncode,
        }
    except FileNotFoundError:
        logger.error("uncover binary not found at '%s'", UNCOVER_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"uncover binary not found at '{UNCOVER_BIN}'. Ensure uncover is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("uncover command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"uncover command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("uncover command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def search_hosts(
    query: str,
    engines: str = "shodan-idb",
    fields: str = "ip,port,host",
    limit: int = 100,
    json_output: bool = True,
) -> dict:
    """Search for exposed hosts using internet search engines.

    Uses Uncover to query services like Shodan, Censys, FOFA, Hunter, Quake,
    and others to discover exposed hosts matching the given query.

    Args:
        query: Search query string (e.g. "nginx", "Apache port:443", "org:Google").
        engines: Comma-separated search engines to use. Options: shodan, shodan-idb, censys, fofa, hunter, quake, zoomeye, netlas, criminalip. Default "shodan-idb".
        fields: Comma-separated output fields. Options: ip, port, host. Default "ip,port,host".
        limit: Maximum number of results to return. Default 100.
        json_output: If True, return results in JSON format. Default True.

    Returns:
        Dictionary with discovered hosts and metadata.
    """
    logger.info("search_hosts called with query=%s, engines=%s", query, engines)
    key_warning = _check_engine_keys(engines)
    if key_warning:
        logger.warning(key_warning)

    args = ["-query", query, "-engine", engines, "-field", fields, "-limit", str(limit)]

    if json_output:
        args.append("-json")

    return _run_uncover(args)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8107"))
    logger.info("Starting uncover-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
