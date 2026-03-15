"""
Masscan Tool for LangChain Agents

Fast Internet-scale port scanner. Runs inside the project's osint-tools Docker
container via shared.modules.tools.docker_client.execute_in_docker. Use for
large-scale port scanning and network reconnaissance (e.g. CIDR ranges).

Docker: Requires the osint-tools container (see shared/modules/tools/docker).
The chat/solo process must have Docker socket access. Returns JSON errors when
Docker is unavailable or masscan fails.
"""

import json
import re
from typing import List, Dict, Any
from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState
from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/masscan_tool.log")


class MasscanSecurityAgentState(AgentState):
    """Extended agent state for Masscan operations."""
    user_id: str = ""


# -oL list format: "Host: <IP> () Ports: <PORT>/open/tcp////" per line
_HOST_PORTS_RE = re.compile(r"^Host:\s*(\S+)\s+\(\)\s+Ports:\s*(\d+)/(open|closed)/(tcp|udp)/")
# Alternate format (some versions): "open tcp 80 192.168.1.1 1234567890"
_OPEN_TCP_RE = re.compile(r"^(open|closed)\s+(tcp|udp)\s+(\d+)\s+(\S+)\s+(\d+)\s*$")


def _parse_masscan_list_output(stdout: str) -> List[Dict[str, Any]]:
    """
    Parse masscan -oL (list) output into a list of open-port entries.
    Supports: "Host: <IP> () Ports: <PORT>/open/tcp////" and "open tcp <port> <ip> <ts>".
    Resilient to None/empty stdout and malformed lines (skips with debug log).
    """
    entries: List[Dict[str, Any]] = []
    if not stdout or not isinstance(stdout, str):
        return entries
    for line in stdout.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _HOST_PORTS_RE.match(line)
        if m:
            ip, port_str, status, proto = m.groups()
            try:
                port = int(port_str)
            except ValueError:
                safe_log_debug(logger, "[masscan_scan] Parse skip: invalid port", line=line[:80])
                continue
            entries.append({
                "status": status,
                "proto": proto,
                "port": port,
                "ip": ip,
                "timestamp": "",
            })
            continue
        m = _OPEN_TCP_RE.match(line)
        if m:
            status, proto, port_str, ip, ts = m.groups()
            try:
                port = int(port_str)
            except ValueError:
                safe_log_debug(logger, "[masscan_scan] Parse skip: invalid port", line=line[:80])
                continue
            entries.append({
                "status": status,
                "proto": proto,
                "port": port,
                "ip": ip,
                "timestamp": ts,
            })
    return entries


@tool
def masscan_scan(
    runtime: ToolRuntime,
    ip_range: str,
    ports: str,
    rate: int = 1000
) -> str:
    """
    Fast Internet-scale port scanner using Masscan (runs in Docker).

    Use for large-scale port scanning and network reconnaissance. Scans an IP
    range (CIDR or single IP) for open ports. Ports can be comma-separated
    (e.g. "80,443") or a range (e.g. "1-1000"). Requires the osint-tools
    Docker container.

    Args:
        runtime: ToolRuntime instance (automatically injected by the agent).
        ip_range: IP range to scan (e.g. "192.168.1.0/24" or "10.0.0.1").
        ports: Ports to scan (e.g. "80,443" or "1-1000").
        rate: Packets per second (1-10000000). Default 1000.

    Returns:
        JSON string with keys: status, ip_range, ports, rate, open_ports
        (list of {ip, port, proto, status}), count, summary.
    """
    ip_range_val = ip_range
    try:
        safe_log_info(logger, "[masscan_scan] Starting",
                     ip_range=ip_range,
                     ports=ports,
                     rate=rate)

        # Validate inputs
        if not ip_range or not isinstance(ip_range, str) or len(ip_range.strip()) == 0:
            error_msg = "ip_range must be a non-empty string"
            safe_log_error(logger, "[masscan_scan] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        ip_range_val = ip_range.strip()

        if not ports or not isinstance(ports, str) or len(ports.strip()) == 0:
            error_msg = "ports must be a non-empty string"
            safe_log_error(logger, "[masscan_scan] Validation failed", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        ports = ports.strip()

        if rate < 1 or rate > 10000000:
            error_msg = "rate must be between 1 and 10000000"
            safe_log_error(logger, "[masscan_scan] Validation failed", error_msg=error_msg, rate=rate)
            return json.dumps({"status": "error", "message": error_msg})

        safe_log_debug(logger, "[masscan_scan] Inputs validated",
                      ip_range=ip_range_val,
                      ports=ports,
                      rate=rate)

        docker_client = get_docker_client()
        if docker_client is None:
            safe_log_debug(logger, "[masscan_scan] Docker client is None")
        is_available = docker_client.docker_available if docker_client else False
        safe_log_debug(logger, "[masscan_scan] Docker availability check", docker_available=is_available)

        if not docker_client or not is_available:
            error_msg = (
                "Docker is required for OSINT tools. Setup:\n"
                "1. Build Docker image: cd shared/modules/tools/docker && docker build -t osint-tools:latest .\n"
                "2. Start container: docker-compose up -d"
            )
            safe_log_error(logger, "[masscan_scan] Docker not available", error_msg=error_msg)
            return json.dumps({"status": "error", "message": error_msg})

        # Build masscan CLI args: masscan <ip_range> -p<ports> --rate=<rate> -oL -
        args = [
            ip_range_val,
            "-p", ports,
            "--rate", str(rate),
            "-oL", "-",
        ]
        timeout = 600  # 10 minutes for large ranges
        safe_log_info(logger, "[masscan_scan] Executing in Docker", ip_range=ip_range_val, ports=ports, timeout=timeout)
        docker_result = execute_in_docker("masscan", args, timeout=timeout)

        returncode = docker_result.get("returncode", -1)
        stdout_out = docker_result.get("stdout") if docker_result.get("stdout") is not None else ""
        stderr_out = docker_result.get("stderr") if docker_result.get("stderr") is not None else ""
        if not isinstance(stdout_out, str):
            stdout_out = str(stdout_out) if stdout_out else ""
        if not isinstance(stderr_out, str):
            stderr_out = str(stderr_out) if stderr_out else ""

        if docker_result.get("status") == "error" and returncode == -1:
            error_msg = docker_result.get("message", "Docker execution failed")
            safe_log_error(logger, "[masscan_scan] Docker execution error", error=error_msg, returncode=returncode)
            return json.dumps({"status": "error", "message": error_msg, "returncode": returncode})

        if returncode not in (0, 1):
            error_parts = [f"Masscan exited with code {returncode}"]
            if stderr_out and stderr_out.strip():
                error_parts.append(f"stderr: {stderr_out.strip()[:500]}")
            if docker_result.get("message"):
                error_parts.append(docker_result.get("message"))
            error_msg = ". ".join(error_parts)
            safe_log_error(logger, "[masscan_scan] Execution failed", error=error_msg, returncode=returncode)
            return json.dumps({"status": "error", "message": error_msg, "returncode": returncode})

        try:
            entries = _parse_masscan_list_output(stdout_out)
        except Exception as parse_err:
            safe_log_error(logger, "[masscan_scan] Parse output failed", error=str(parse_err), exc_info=True)
            return json.dumps({
                "status": "error",
                "message": f"Failed to parse masscan output: {str(parse_err)}",
                "ip_range": ip_range_val,
                "ports": ports,
            })

        open_entries = [e for e in entries if e.get("status") == "open"]

        result = {
            "status": "success",
            "ip_range": ip_range_val,
            "ports": ports,
            "rate": rate,
            "open_ports": open_entries,
            "count": len(open_entries),
            "summary": f"Found {len(open_entries)} open port(s) on {ip_range_val} for ports {ports}.",
        }
        safe_log_info(logger, "[masscan_scan] Complete",
                     ip_range=ip_range_val, count=len(open_entries))
        return json.dumps(result, indent=2)

    except Exception as e:
        safe_log_error(logger, "[masscan_scan] Error",
                      exc_info=True,
                      error=str(e),
                      ip_range=ip_range_val)
        return json.dumps({"status": "error", "message": f"Masscan scan failed: {str(e)}"})
