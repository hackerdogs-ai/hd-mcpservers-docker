"""
AbuseCH (abuse.ch) Threat Intelligence Tools for LangChain Agents

This module provides LangChain tools that wrap the AbuseCH MCP implementation found
in `shared/modules/tools/osint/abusech-mcp-main/`.

Covered services (via the AbuseCH unified layer):
- MalwareBazaar (hash/file intelligence)
- URLhaus (URL/host/payload intelligence)
- ThreatFox (IOC intelligence)

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

These tools require an AbuseCH API key.

IMPORTANT: Do NOT rely on process environment variables for agent execution.
Keys should be provided via ToolRuntime (preferred), following the established
pattern used across Hackerdogs tools.

Retrieval Priority (in order):
1) PRIMARY: runtime.state["environment_variables"][<instance>]["ABUSECH_API_KEY"]
   - Searches through all instances inside the environment_variables dict
   - First match wins
2) SECONDARY: runtime.state["api_keys"]["ABUSECH_API_KEY"]

Security Notes:
- API keys are masked in logs. Never log raw keys.
- Some IOCs may be sensitive; logs are kept minimal and should be redacted in production.
"""

from __future__ import annotations

import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Optional

from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_error, safe_log_info, mask_api_key

logger = setup_logger(__name__, log_file_path="logs/abusech_tool.log")


# --- Import the attached AbuseCH MCP implementation (non-package folder) ---
_ABUSECH_MCP_DIR = Path(__file__).resolve().parent / "abusech-mcp-main"
if _ABUSECH_MCP_DIR.exists() and str(_ABUSECH_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_ABUSECH_MCP_DIR))

try:
    import abusech_intel  # type: ignore
except Exception as e:  # pragma: no cover
    abusech_intel = None  # type: ignore
    safe_log_error(logger, "[abusech_langchain] Failed to import abusech_intel", exc_info=True, error=str(e))


class AbuseCHSecurityAgentState(AgentState):
    """Extended agent state for AbuseCH operations."""

    user_id: str = ""


def _get_api_key_from_runtime(runtime: ToolRuntime, key_name: str) -> Optional[str]:
    """
    Retrieve an API key from ToolRuntime state.

    Key resolution order:
    1) runtime.state["environment_variables"][<instance>][key_name]
    2) runtime.state["api_keys"][key_name]
    """
    if not runtime or not getattr(runtime, "state", None):
        return None

    # PRIMARY: runtime.state.environment_variables[<instance>][KEY]
    env_vars_dict = runtime.state.get("environment_variables", {})
    if isinstance(env_vars_dict, dict):
        for instance_name, env_vars in env_vars_dict.items():
            if not isinstance(env_vars, dict):
                continue
            val = env_vars.get(key_name)
            if val:
                safe_log_info(
                    logger,
                    "[_get_api_key_from_runtime] Found API key in runtime env",
                    key_name=key_name,
                    instance_name=instance_name,
                    api_key_masked=mask_api_key(str(val)),
                )
                return str(val)

    # SECONDARY: runtime.state.api_keys[KEY]
    api_keys_dict = runtime.state.get("api_keys", {})
    if isinstance(api_keys_dict, dict):
        val = api_keys_dict.get(key_name)
        if val:
            safe_log_info(
                logger,
                "[_get_api_key_from_runtime] Found API key in runtime api_keys",
                key_name=key_name,
                api_key_masked=mask_api_key(str(val)),
            )
            return str(val)

    return None


def _run_coro_in_new_thread(coro) -> Any:
    """
    Run an async coroutine in a dedicated thread.

    This avoids 'asyncio.run() cannot be called from a running event loop' when tools
    are invoked from async contexts.
    """
    with ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(lambda: asyncio.run(coro))
        return fut.result()


def _ensure_backend_loaded() -> Optional[str]:
    """
    Ensure the AbuseCH backend (abusech_intel) is importable.
    Returns an error message if it isn't.
    """
    if abusech_intel is None:
        return (
            "AbuseCH backend is not available (failed to import abusech_intel). "
            "Ensure dependencies for abusech-mcp-main are installed and imports resolve."
        )
    return None


@tool
def abusech_ip_report(runtime: ToolRuntime, ip: str) -> str:
    """
    Get a comprehensive IP report from AbuseCH sources (URLhaus host + ThreatFox IOC).

    Requires:
      ABUSECH_API_KEY (via ToolRuntime).
    """
    try:
        backend_err = _ensure_backend_loaded()
        if backend_err:
            return json.dumps({"status": "error", "message": backend_err})

        if not ip or not isinstance(ip, str):
            return json.dumps({"status": "error", "message": "ip must be a non-empty string"})

        api_key = _get_api_key_from_runtime(runtime, "ABUSECH_API_KEY")
        if not api_key:
            return json.dumps({"status": "error", "message": "ABUSECH_API_KEY not found in ToolRuntime"})

        safe_log_info(logger, "[abusech_ip_report] Starting", ip=ip, api_key_masked=mask_api_key(api_key))

        coro = abusech_intel._get_ip_report(ip=ip, abusech_api_key=api_key)  # type: ignore[attr-defined]
        data = _run_coro_in_new_thread(coro)
        if isinstance(data, dict) and data.get("error"):
            return json.dumps({"status": "error", "message": data.get("error"), "ip": ip, "raw_response": data}, indent=2)
        return json.dumps({"status": "success", "ip": ip, "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abusech_ip_report] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"AbuseCH IP report failed: {str(e)}"})


@tool
def abusech_domain_report(runtime: ToolRuntime, domain: str) -> str:
    """
    Get a comprehensive domain report from AbuseCH sources (URLhaus host + ThreatFox IOC).

    Requires:
      ABUSECH_API_KEY (via ToolRuntime).
    """
    try:
        backend_err = _ensure_backend_loaded()
        if backend_err:
            return json.dumps({"status": "error", "message": backend_err})

        if not domain or not isinstance(domain, str):
            return json.dumps({"status": "error", "message": "domain must be a non-empty string"})

        api_key = _get_api_key_from_runtime(runtime, "ABUSECH_API_KEY")
        if not api_key:
            return json.dumps({"status": "error", "message": "ABUSECH_API_KEY not found in ToolRuntime"})

        safe_log_info(logger, "[abusech_domain_report] Starting", domain=domain, api_key_masked=mask_api_key(api_key))

        coro = abusech_intel._get_domain_report(domain=domain, abusech_api_key=api_key)  # type: ignore[attr-defined]
        data = _run_coro_in_new_thread(coro)
        if isinstance(data, dict) and data.get("error"):
            return json.dumps(
                {"status": "error", "message": data.get("error"), "queried_domain": domain, "raw_response": data}, indent=2
            )
        # Ensure the queried domain is always present and matches the input
        if isinstance(data, dict):
            data["queried_domain"] = domain
            # Log a warning if URLhaus returned a different host
            if data.get("urlhaus_host") and data["urlhaus_host"] != domain:
                safe_log_info(
                    logger,
                    "[abusech_domain_report] URLhaus host differs from queried domain",
                    queried_domain=domain,
                    urlhaus_host=data.get("urlhaus_host"),
                )
        return json.dumps({"status": "success", "queried_domain": domain, "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abusech_domain_report] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"AbuseCH domain report failed: {str(e)}"})


@tool
def abusech_url_report(runtime: ToolRuntime, url: str) -> str:
    """
    Get a comprehensive URL report from AbuseCH sources (URLhaus URL intelligence).

    Requires:
      ABUSECH_API_KEY (via ToolRuntime).
    """
    try:
        backend_err = _ensure_backend_loaded()
        if backend_err:
            return json.dumps({"status": "error", "message": backend_err})

        if not url or not isinstance(url, str):
            return json.dumps({"status": "error", "message": "url must be a non-empty string"})

        api_key = _get_api_key_from_runtime(runtime, "ABUSECH_API_KEY")
        if not api_key:
            return json.dumps({"status": "error", "message": "ABUSECH_API_KEY not found in ToolRuntime"})

        safe_log_info(logger, "[abusech_url_report] Starting", url=url, api_key_masked=mask_api_key(api_key))

        coro = abusech_intel._get_url_report(url=url, abusech_api_key=api_key)  # type: ignore[attr-defined]
        data = _run_coro_in_new_thread(coro)
        if isinstance(data, dict) and data.get("error"):
            return json.dumps({"status": "error", "message": data.get("error"), "url": url, "raw_response": data}, indent=2)
        return json.dumps({"status": "success", "url": url, "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abusech_url_report] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"AbuseCH URL report failed: {str(e)}"})


@tool
def abusech_file_report(runtime: ToolRuntime, hash_value: str) -> str:
    """
    Get a comprehensive file report by hash from AbuseCH sources:
    - MalwareBazaar (hash report)
    - URLhaus (payload report for MD5/SHA256)
    - ThreatFox (hash report)

    Requires:
      ABUSECH_API_KEY (via ToolRuntime).
    """
    try:
        backend_err = _ensure_backend_loaded()
        if backend_err:
            return json.dumps({"status": "error", "message": backend_err})

        if not hash_value or not isinstance(hash_value, str):
            return json.dumps({"status": "error", "message": "hash_value must be a non-empty string"})

        api_key = _get_api_key_from_runtime(runtime, "ABUSECH_API_KEY")
        if not api_key:
            return json.dumps({"status": "error", "message": "ABUSECH_API_KEY not found in ToolRuntime"})

        safe_log_info(
            logger,
            "[abusech_file_report] Starting",
            hash_value=hash_value,
            api_key_masked=mask_api_key(api_key),
        )

        coro = abusech_intel._get_file_report(hash_value=hash_value, abusech_api_key=api_key)  # type: ignore[attr-defined]
        data = _run_coro_in_new_thread(coro)
        if isinstance(data, dict) and data.get("error"):
            return json.dumps(
                {"status": "error", "message": data.get("error"), "hash": hash_value, "raw_response": data}, indent=2
            )
        return json.dumps({"status": "success", "hash": hash_value, "raw_response": data}, indent=2)
    except Exception as e:
        safe_log_error(logger, "[abusech_file_report] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"AbuseCH file report failed: {str(e)}"})


