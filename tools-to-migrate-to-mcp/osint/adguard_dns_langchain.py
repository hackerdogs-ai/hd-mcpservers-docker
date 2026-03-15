"""
AdGuard DNS block check (LangChain Tool)

Migrated from SpiderFoot plugin `sfp_adguard_dns`:
- Queries AdGuard DNS resolvers for a hostname
- If the response includes 94.140.14.35, the host is considered blocked

No API key required.

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

Optional ToolRuntime keys (resolution order like other tools):
1) runtime.state["environment_variables"][<instance>][KEY]
2) runtime.state["environment_variables"][KEY] (flat dict)

Supported keys:
- ADGUARD_DNS_DEFAULT_NS: comma-separated IPs (default: "94.140.14.14,94.140.15.15")
- ADGUARD_DNS_FAMILY_NS: comma-separated IPs (default: "94.140.14.15,94.140.15.16")
- ADGUARD_DNS_TIMEOUT: integer seconds (default: 5)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional

import dns.resolver
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info


logger = setup_logger(__name__, log_file_path="logs/adguard_dns_tool.log")

Mode = Literal["default", "family", "both"]

_DEFAULT_NS_DEFAULT = ["94.140.14.14", "94.140.15.15"]
_DEFAULT_NS_FAMILY = ["94.140.14.15", "94.140.15.16"]
_BLOCKED_IP = "94.140.14.35"
_DEFAULT_TIMEOUT = 5


def _json_ok(data: Dict[str, Any]) -> str:
    return json.dumps({"status": "ok", **data}, indent=2)


def _json_error(message: str, *, error_type: str = "error", details: Optional[Dict[str, Any]] = None) -> str:
    out: Dict[str, Any] = {"status": "error", "message": message, "error_type": error_type}
    if details:
        out["details"] = details
    return json.dumps(out, indent=2)


def _get_runtime_env(runtime: ToolRuntime, key: str) -> Optional[str]:
    try:
        if not runtime or not getattr(runtime, "state", None):
            return None
        env_vars = runtime.state.get("environment_variables", {})
        if isinstance(env_vars, dict):
            for _, inst_env in env_vars.items():
                if isinstance(inst_env, dict) and inst_env.get(key):
                    return str(inst_env.get(key))
            if env_vars.get(key):
                return str(env_vars.get(key))
    except Exception:
        return None
    return None


def _parse_nameserver_list(value: Optional[str], default: List[str]) -> List[str]:
    if not value:
        return default
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return parts or default


def _resolve_a(host: str, nameservers: List[str], timeout_s: int) -> List[str]:
    res = dns.resolver.Resolver(configure=True)
    res.nameservers = nameservers
    res.lifetime = timeout_s
    res.timeout = timeout_s
    answers = res.resolve(host, "A")
    ips: List[str] = []
    for rdata in answers:
        ips.append(str(rdata))
    return ips


@tool
def adguard_dns_check_host(
    runtime: ToolRuntime,
    host: str,
    mode: Mode = "both",
) -> str:
    """
    Check whether a host would be blocked by AdGuard DNS.

    Returns `blocked_default` / `blocked_family` based on whether the A record set contains 94.140.14.35.
    """
    try:
        safe_log_info(logger, "[adguard_dns_check_host] Starting", host=host, mode=mode)
        if not host or not isinstance(host, str):
            return _json_error("host must be a non-empty string", error_type="validation_error")
        if mode not in ("default", "family", "both"):
            return _json_error("mode must be one of: default, family, both", error_type="validation_error")

        timeout_s = _DEFAULT_TIMEOUT
        rt_timeout = _get_runtime_env(runtime, "ADGUARD_DNS_TIMEOUT")
        if rt_timeout:
            try:
                timeout_s = max(1, min(30, int(rt_timeout)))
            except Exception:
                timeout_s = _DEFAULT_TIMEOUT

        ns_default = _parse_nameserver_list(_get_runtime_env(runtime, "ADGUARD_DNS_DEFAULT_NS"), _DEFAULT_NS_DEFAULT)
        ns_family = _parse_nameserver_list(_get_runtime_env(runtime, "ADGUARD_DNS_FAMILY_NS"), _DEFAULT_NS_FAMILY)

        out: Dict[str, Any] = {
            "host": host,
            "mode": mode,
            "blocked_default": None,
            "blocked_family": None,
            "answers_default": None,
            "answers_family": None,
            "blocked_ip": _BLOCKED_IP,
        }

        if mode in ("default", "both"):
            try:
                ips = _resolve_a(host, ns_default, timeout_s)
                out["answers_default"] = ips
                out["blocked_default"] = _BLOCKED_IP in ips
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                out["answers_default"] = []
                out["blocked_default"] = False
            except dns.exception.Timeout:
                out["answers_default"] = None
                out["blocked_default"] = None
            except Exception as e:
                safe_log_error(logger, "[adguard_dns_check_host] Default resolver error", exc_info=True, error=str(e))
                out["answers_default"] = None
                out["blocked_default"] = None

        if mode in ("family", "both"):
            try:
                ips = _resolve_a(host, ns_family, timeout_s)
                out["answers_family"] = ips
                out["blocked_family"] = _BLOCKED_IP in ips
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                out["answers_family"] = []
                out["blocked_family"] = False
            except dns.exception.Timeout:
                out["answers_family"] = None
                out["blocked_family"] = None
            except Exception as e:
                safe_log_error(logger, "[adguard_dns_check_host] Family resolver error", exc_info=True, error=str(e))
                out["answers_family"] = None
                out["blocked_family"] = None

        safe_log_debug(logger, "[adguard_dns_check_host] Completed", result=out)
        return _json_ok(out)

    except Exception as e:
        safe_log_error(logger, "[adguard_dns_check_host] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}", error_type="unexpected_error")



