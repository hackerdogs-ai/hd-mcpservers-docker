"""Brutus MCP Server - Credential Testing via FastMCP."""

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
logger = logging.getLogger("brutus-mcp")

mcp = FastMCP(
    "brutus-mcp",
    instructions="MCP server for Brutus - tests credentials across 24 protocols (SSH, RDP, MySQL, PostgreSQL, Redis, SMB, HTTP Basic Auth, etc.) with pipeline support.",
)

BRUTUS_BIN = shutil.which("brutus") or "brutus"


def _run_brutus(args: list[str], timeout: int = 60) -> dict:
    """Execute brutus CLI and return structured result."""
    try:
        result = subprocess.run(
            [BRUTUS_BIN] + args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0:
            logger.warning("brutus exited with code %d: %s", result.returncode, stderr)

        parsed = None
        if output:
            try:
                parsed = json.loads(output)
            except json.JSONDecodeError:
                lines = output.splitlines()
                json_results = []
                for line in lines:
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
        logger.error("brutus binary not found at '%s'", BRUTUS_BIN)
        return {
            "success": False,
            "output": None,
            "stderr": f"brutus binary not found at '{BRUTUS_BIN}'. Ensure brutus is installed.",
            "exit_code": -1,
        }
    except subprocess.TimeoutExpired:
        logger.error("brutus command timed out after %ds", timeout)
        return {
            "success": False,
            "output": None,
            "stderr": f"brutus command timed out after {timeout}s",
            "exit_code": -1,
        }
    except Exception as exc:
        logger.error("brutus command failed: %s", exc)
        return {
            "success": False,
            "output": None,
            "stderr": str(exc),
            "exit_code": -1,
        }


@mcp.tool()
def test_credentials(
    target: str,
    protocol: str,
    usernames: str = "",
    passwords: str = "",
    threads: int = 4,
    json_output: bool = True,
    verbose: bool = False,
) -> dict:
    """Test credentials against a target host across supported protocols.

    Brutus supports 24 protocols including SSH, RDP, MySQL, PostgreSQL, Redis,
    SMB, HTTP Basic Auth, FTP, Telnet, LDAP, SNMP, VNC, and more.

    Args:
        target: Target in host:port format (e.g. "192.168.1.1:22").
        protocol: Protocol to test (e.g. "ssh", "rdp", "mysql", "postgres", "redis", "smb", "http-basic", "ftp", "telnet", "ldap", "snmp", "vnc").
        usernames: Comma-separated list of usernames to test.
        passwords: Comma-separated list of passwords to test.
        threads: Number of concurrent threads. Default 4.
        json_output: If True, request JSON output from brutus. Default True.
        verbose: If True, enable verbose output. Default False.

    Returns:
        Dictionary with credential testing results including any successful logins.
    """
    logger.info("test_credentials called with target=%s, protocol=%s", target, protocol)
    args = ["--target", target, "--protocol", protocol]

    if usernames:
        for u in usernames.split(","):
            u = u.strip()
            if u:
                args.extend(["-u", u])

    if passwords:
        for p in passwords.split(","):
            p = p.strip()
            if p:
                args.extend(["-p", p])

    args.extend(["-t", str(threads)])

    if json_output:
        args.append("--json")

    if verbose:
        args.append("-v")

    overall_timeout = max(threads * 15, 60)
    return _run_brutus(args, timeout=overall_timeout)


@mcp.tool()
def check_rdp_nla(
    target: str,
    verbose: bool = False,
) -> dict:
    """Check if an RDP target has Network Level Authentication (NLA) enabled.

    NLA requires valid credentials before the RDP session is established,
    which affects brute-force feasibility. This probes the RDP endpoint
    to determine its NLA configuration.

    Args:
        target: Target in host:port format (e.g. "192.168.1.1:3389").
        verbose: If True, enable verbose output. Default False.

    Returns:
        Dictionary with NLA detection results.
    """
    logger.info("check_rdp_nla called with target=%s", target)
    args = ["--target", target, "--protocol", "rdp", "--json"]

    if verbose:
        args.append("-v")

    args.extend(["-u", "nla_check", "-p", "nla_check", "-t", "1"])

    return _run_brutus(args, timeout=30)


@mcp.tool()
def detect_sticky_keys(
    target: str,
    verbose: bool = False,
) -> dict:
    """Detect RDP sticky keys backdoor on a target.

    The sticky keys backdoor replaces sethc.exe with cmd.exe, allowing
    unauthenticated command execution at the RDP login screen by pressing
    Shift five times. This check probes for that condition.

    Args:
        target: Target in host:port format (e.g. "192.168.1.1:3389").
        verbose: If True, enable verbose output. Default False.

    Returns:
        Dictionary with sticky keys detection results.
    """
    logger.info("detect_sticky_keys called with target=%s", target)
    args = ["--target", target, "--protocol", "rdp", "--json"]

    if verbose:
        args.append("-v")

    args.extend(["-u", "sticky_keys_check", "-p", "sticky_keys_check", "-t", "1"])

    return _run_brutus(args, timeout=30)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    port = int(os.environ.get("MCP_PORT", "8102"))
    logger.info("Starting brutus-mcp server (transport=%s, port=%s)", transport, port)

    if transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    else:
        mcp.run(transport="stdio", show_banner=False)
