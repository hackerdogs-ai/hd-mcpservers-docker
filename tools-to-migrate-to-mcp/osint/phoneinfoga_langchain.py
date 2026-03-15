"""
PhoneInfoga Tools for LangChain Agents

Phone number OSINT using PhoneInfoga scanners:
- local
- numverify
- googlesearch
- googlecse
- ovh

References:
- Installation (Docker): https://sundowndev.github.io/phoneinfoga/getting-started/install/
- Scanners: https://sundowndev.github.io/phoneinfoga/getting-started/scanners/
- CLI usage: https://sundowndev.github.io/phoneinfoga/getting-started/usage/
- GitHub: https://github.com/sundowndev/phoneinfoga

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

This tool requires the following configuration:

1. Docker Environment (Required)
   - PhoneInfoga runs via its official Docker image.
   - NOTE: The upstream image may be amd64-only; on Apple Silicon we run with:
     --platform=linux/amd64

2. Optional scanner credentials (via ToolRuntime.state)

   These values should be provided via `runtime.state` (LangChain ToolRuntime),
   matching the pattern used by other tools like `browserless_langchain.py`.

   Retrieval Priority (in order):
   1) PRIMARY: runtime.state["environment_variables"][<instance>][KEY]
      - Searches through all instances inside the environment_variables dict
      - First match wins per key
   2) SECONDARY: runtime.state["api_keys"][KEY]  (API keys only)

   Supported keys (documented):

   - NUMVERIFY_API_KEY (Numverify / ApiLayer token)
     - Used by scanner: `numverify`
     - Purpose: Enriches the phone number with country code, location, carrier, line type, etc.
     - Example (runtime.state):
       runtime.state["environment_variables"] = {
         "phoneinfoga_instance": {
           "NUMVERIFY_API_KEY": "your_apilayer_token"
         }
       }

   - GOOGLE_API_KEY (Google API token)
     - Used by scanner: `googlecse`
     - Purpose: Authenticates to Google Custom Search JSON API
     - Example (runtime.state):
       runtime.state["environment_variables"] = {
         "phoneinfoga_instance": {
           "GOOGLE_API_KEY": "your_google_api_key"
         }
       }

   - GOOGLECSE_CX (Google Custom Search Engine ID)
     - Used by scanner: `googlecse`
     - Purpose: Specifies which programmable search engine to use
     - Example (runtime.state):
       runtime.state["environment_variables"] = {
         "phoneinfoga_instance": {
           "GOOGLECSE_CX": "your_cse_id"
         }
       }

   - GOOGLECSE_MAX_RESULTS (integer as string, 1-100; default: 10)
     - Used by scanner: `googlecse`
     - Purpose: Controls how many results are returned per request (higher values may cost more)
     - Note: If the tool call leaves `googlecse_max_results` at the default (10), and this runtime
       key is provided, the runtime value is used.
     - Example (runtime.state):
       runtime.state["environment_variables"] = {
         "phoneinfoga_instance": {
           "GOOGLECSE_MAX_RESULTS": "10"
         }
       }

Security Notes:
- Phone numbers are treated as sensitive PII; avoid logging full numbers in production.
- API keys are never logged (safe_log_* masks them).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Literal

from langchain.tools import tool, ToolRuntime
from langchain.agents import AgentState

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_info, safe_log_error, safe_log_debug, mask_api_key
from shared.modules.tools.docker_client import get_docker_client, execute_in_docker

logger = setup_logger(__name__, log_file_path="logs/phoneinfoga_tool.log")

ScannerName = Literal["local", "numverify", "googlesearch", "googlecse", "ovh"]
_ALL_SCANNERS: List[str] = ["local", "numverify", "googlesearch", "googlecse", "ovh"]


class PhoneInfogaSecurityAgentState(AgentState):
    """Extended agent state for PhoneInfoga operations."""
    user_id: str = ""


def _check_docker_available() -> bool:
    """Check whether Docker is available."""
    client = get_docker_client()
    return client is not None and client.docker_available


def _get_phoneinfoga_config_from_runtime(runtime: ToolRuntime) -> Dict[str, Any]:
    """
    Retrieve PhoneInfoga scanner configuration from ToolRuntime.

    Follows the same pattern used in tools like `browserless_langchain.py`:
    - PRIMARY: runtime.state["environment_variables"][<instance>][KEY]
    - SECONDARY: runtime.state["api_keys"][KEY] for API keys

    Supported keys:
    - NUMVERIFY_API_KEY
    - GOOGLE_API_KEY
    - GOOGLECSE_CX
    - GOOGLECSE_MAX_RESULTS

    Returns:
        Dict with any found keys. Values may be None if not found.
    """
    cfg: Dict[str, Any] = {}
    if not runtime or not getattr(runtime, "state", None):
        return cfg

    env_vars_dict = runtime.state.get("environment_variables", {})
    instances_count = len(env_vars_dict) if isinstance(env_vars_dict, dict) else 0
    safe_log_debug(
        logger,
        "[_get_phoneinfoga_config_from_runtime] Starting config retrieval",
        instances_count=instances_count,
        instance_names=list(env_vars_dict.keys()) if isinstance(env_vars_dict, dict) else [],
    )

    # PRIMARY: search all tool instances for PhoneInfoga-related keys
    if isinstance(env_vars_dict, dict):
        for instance_name, env_vars in env_vars_dict.items():
            if not isinstance(env_vars, dict):
                continue

            # Collect keys if present; first match wins per key
            if "NUMVERIFY_API_KEY" not in cfg and env_vars.get("NUMVERIFY_API_KEY"):
                cfg["NUMVERIFY_API_KEY"] = env_vars.get("NUMVERIFY_API_KEY")
                safe_log_info(
                    logger,
                    "[_get_phoneinfoga_config_from_runtime] Found NUMVERIFY_API_KEY in runtime env",
                    instance_name=instance_name,
                    api_key_masked=mask_api_key(str(cfg["NUMVERIFY_API_KEY"])),
                )
            if "GOOGLE_API_KEY" not in cfg and env_vars.get("GOOGLE_API_KEY"):
                cfg["GOOGLE_API_KEY"] = env_vars.get("GOOGLE_API_KEY")
                safe_log_info(
                    logger,
                    "[_get_phoneinfoga_config_from_runtime] Found GOOGLE_API_KEY in runtime env",
                    instance_name=instance_name,
                    api_key_masked=mask_api_key(str(cfg["GOOGLE_API_KEY"])),
                )
            if "GOOGLECSE_CX" not in cfg and env_vars.get("GOOGLECSE_CX"):
                cfg["GOOGLECSE_CX"] = env_vars.get("GOOGLECSE_CX")
                safe_log_info(
                    logger,
                    "[_get_phoneinfoga_config_from_runtime] Found GOOGLECSE_CX in runtime env",
                    instance_name=instance_name,
                    cx_present=True,
                )
            if "GOOGLECSE_MAX_RESULTS" not in cfg and env_vars.get("GOOGLECSE_MAX_RESULTS"):
                cfg["GOOGLECSE_MAX_RESULTS"] = env_vars.get("GOOGLECSE_MAX_RESULTS")
                safe_log_info(
                    logger,
                    "[_get_phoneinfoga_config_from_runtime] Found GOOGLECSE_MAX_RESULTS in runtime env",
                    instance_name=instance_name,
                    googlecse_max_results=env_vars.get("GOOGLECSE_MAX_RESULTS"),
                )

    # SECONDARY: api_keys dict (only for API keys)
    api_keys_dict = runtime.state.get("api_keys", {}) if runtime and runtime.state else {}
    if isinstance(api_keys_dict, dict):
        if "NUMVERIFY_API_KEY" not in cfg and api_keys_dict.get("NUMVERIFY_API_KEY"):
            cfg["NUMVERIFY_API_KEY"] = api_keys_dict.get("NUMVERIFY_API_KEY")
            safe_log_info(
                logger,
                "[_get_phoneinfoga_config_from_runtime] Found NUMVERIFY_API_KEY in runtime api_keys",
                api_key_masked=mask_api_key(str(cfg["NUMVERIFY_API_KEY"])),
            )
        if "GOOGLE_API_KEY" not in cfg and api_keys_dict.get("GOOGLE_API_KEY"):
            cfg["GOOGLE_API_KEY"] = api_keys_dict.get("GOOGLE_API_KEY")
            safe_log_info(
                logger,
                "[_get_phoneinfoga_config_from_runtime] Found GOOGLE_API_KEY in runtime api_keys",
                api_key_masked=mask_api_key(str(cfg["GOOGLE_API_KEY"])),
            )
        if "GOOGLECSE_CX" not in cfg and api_keys_dict.get("GOOGLECSE_CX"):
            cfg["GOOGLECSE_CX"] = api_keys_dict.get("GOOGLECSE_CX")
            safe_log_info(
                logger,
                "[_get_phoneinfoga_config_from_runtime] Found GOOGLECSE_CX in runtime api_keys",
                cx_present=True,
            )

    return cfg


def _sanitize_phone_for_logs(phone_number: str) -> str:
    """
    Mask phone numbers for logs (keep last 4 digits if present).
    """
    if not phone_number:
        return ""
    digits = re.sub(r"\D+", "", phone_number)
    if len(digits) <= 4:
        return "[REDACTED]"
    return f"[REDACTED...{digits[-4:]}]"


def _build_disable_flags(only_scanners: Optional[List[str]]) -> List[str]:
    """
    PhoneInfoga CLI supports disabling scanners via -D/--disable.
    To run a single scanner, disable all others.
    """
    if not only_scanners:
        return []
    wanted = set(only_scanners)
    disable = [s for s in _ALL_SCANNERS if s not in wanted]
    flags: List[str] = []
    for s in disable:
        flags.extend(["-D", s])
    return flags


def _parse_kv_block(lines: List[str]) -> Dict[str, Any]:
    """
    Parse blocks with simple `Key: Value` lines.
    """
    out: Dict[str, Any] = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            # keep unstructured lines
            out.setdefault("_raw", []).append(line)
            continue
        k, v = line.split(":", 1)
        key = k.strip()
        val = v.strip()
        # Best-effort type coercion
        if val.lower() in ("true", "false"):
            out[key] = val.lower() == "true"
        else:
            try:
                if re.fullmatch(r"-?\d+", val):
                    out[key] = int(val)
                else:
                    out[key] = val
            except Exception:
                out[key] = val
    return out


def _parse_googlesearch_block(lines: List[str], max_links: int = 50) -> Dict[str, Any]:
    """
    Parse googlesearch output which looks like:
      Social media:
          URL: https://...
      Individuals:
          URL: https://...
    """
    result: Dict[str, Any] = {"categories": {}}
    current_category: Optional[str] = None
    links_count = 0
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.endswith(":") and not line.strip().startswith("URL:"):
            current_category = line.strip()[:-1]
            result["categories"].setdefault(current_category, [])
            continue
        m = re.search(r"URL:\s*(\S+)", line.strip())
        if m and current_category:
            if links_count < max_links:
                result["categories"][current_category].append(m.group(1))
            links_count += 1
    result["links_total"] = links_count
    result["links_returned"] = min(links_count, max_links)
    return result


def _parse_googlecse_block(lines: List[str]) -> Dict[str, Any]:
    """
    Parse googlecse output example:
      Homepage: ...
      Result count: 1
      Items:
          Title: ...
          URL: ...
    """
    header_lines: List[str] = []
    items: List[Dict[str, str]] = []
    current_item: Dict[str, str] = {}
    in_items = False

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line == "Items:":
            in_items = True
            continue
        if not in_items:
            header_lines.append(line)
            continue

        # Items section
        if line.startswith("Title:"):
            if current_item:
                items.append(current_item)
                current_item = {}
            current_item["title"] = line.split(":", 1)[1].strip()
        elif line.startswith("URL:"):
            current_item["url"] = line.split(":", 1)[1].strip()
        else:
            # ignore unknown item lines, but preserve
            current_item.setdefault("_raw", "")
            current_item["_raw"] += (line + "\n")

    if current_item:
        items.append(current_item)

    parsed = _parse_kv_block(header_lines)
    parsed["items"] = items
    parsed["items_count"] = len(items)
    return parsed


def _parse_phoneinfoga_stdout(stdout: str, max_google_links: int = 50) -> Dict[str, Any]:
    """
    Parse PhoneInfoga CLI stdout into structured JSON by scanner.

    We segment by headers: "Results for <scanner>".
    """
    results: Dict[str, Any] = {}
    current_scanner: Optional[str] = None
    buf: List[str] = []

    def flush():
        nonlocal buf, current_scanner
        if not current_scanner:
            buf = []
            return
        # Parse based on scanner type
        if current_scanner == "googlesearch":
            results[current_scanner] = _parse_googlesearch_block(buf, max_links=max_google_links)
        elif current_scanner == "googlecse":
            results[current_scanner] = _parse_googlecse_block(buf)
        else:
            results[current_scanner] = _parse_kv_block(buf)
        buf = []

    for raw_line in stdout.splitlines():
        line = raw_line.rstrip("\n")
        m = re.match(r"^Results for\s+([a-zA-Z0-9_]+)\s*$", line.strip())
        if m:
            flush()
            current_scanner = m.group(1).strip()
            continue
        # Collect lines inside a scanner section
        if current_scanner:
            buf.append(line)

    flush()
    return results


def _phoneinfoga_env(
    numverify_api_key: Optional[str],
    google_api_key: Optional[str],
    googlecse_cx: Optional[str],
    googlecse_max_results: int,
) -> Dict[str, str]:
    env: Dict[str, str] = {}
    if numverify_api_key:
        env["NUMVERIFY_API_KEY"] = numverify_api_key
    if google_api_key:
        env["GOOGLE_API_KEY"] = google_api_key
    if googlecse_cx:
        env["GOOGLECSE_CX"] = googlecse_cx
    if googlecse_max_results:
        env["GOOGLECSE_MAX_RESULTS"] = str(googlecse_max_results)
    return env


def _run_phoneinfoga_scan(
    phone_number: str,
    only_scanners: Optional[List[str]] = None,
    numverify_api_key: Optional[str] = None,
    google_api_key: Optional[str] = None,
    googlecse_cx: Optional[str] = None,
    googlecse_max_results: int = 10,
    plugin_paths: Optional[List[str]] = None,
    timeout: int = 120,
    max_google_links: int = 50,
) -> str:
    """
    Run PhoneInfoga scan in Docker and return structured JSON as a string.
    """
    # Validate scanner selection
    if only_scanners:
        invalid = [s for s in only_scanners if s not in _ALL_SCANNERS]
        if invalid:
            return json.dumps({"status": "error", "message": f"Invalid scanners: {invalid}. Valid: {_ALL_SCANNERS}"})

    if not phone_number or not isinstance(phone_number, str) or len(phone_number.strip()) == 0:
        return json.dumps({"status": "error", "message": "phone_number must be a non-empty string"})

    if googlecse_max_results < 1 or googlecse_max_results > 100:
        return json.dumps({"status": "error", "message": "googlecse_max_results must be between 1 and 100"})

    if max_google_links < 1 or max_google_links > 500:
        return json.dumps({"status": "error", "message": "max_google_links must be between 1 and 500"})

    if not _check_docker_available():
        error_msg = (
            "Docker is required for OSINT tools. Setup:\n"
            "1. Ensure Docker is running: docker ps\n"
            "2. PhoneInfoga image will be pulled automatically (linux/amd64 may be required on Apple Silicon)"
        )
        return json.dumps({"status": "error", "message": error_msg})

    args: List[str] = ["scan", "-n", phone_number]
    args.extend(_build_disable_flags(only_scanners))

    # Optional plugins
    if plugin_paths:
        for p in plugin_paths:
            if p:
                args.extend(["--plugin", p])

    env = _phoneinfoga_env(numverify_api_key, google_api_key, googlecse_cx, googlecse_max_results)

    # PhoneInfoga official image can be amd64-only; force linux/amd64 for consistency
    docker_result = execute_in_docker(
        "phoneinfoga",
        args,
        timeout=timeout,
        volumes=None,
        env=env if env else None,
        platform="linux/amd64",
    )

    if docker_result.get("status") != "success":
        detail = docker_result.get("message") or docker_result.get("stderr") or "Unknown error"
        return json.dumps({"status": "error", "message": f"PhoneInfoga failed: {detail}"})

    stdout = docker_result.get("stdout", "") or ""
    stderr = docker_result.get("stderr", "") or ""

    # If stdout is empty, return stderr verbatim
    if not stdout and stderr:
        return json.dumps({"status": "error", "message": stderr})

    parsed = _parse_phoneinfoga_stdout(stdout, max_google_links=max_google_links)

    return json.dumps(
        {
            "status": "success",
            "number": phone_number,
            "scanners_requested": only_scanners if only_scanners else "default",
            "results": parsed,
        },
        indent=2,
    )


@tool
def phoneinfoga_scan(
    runtime: ToolRuntime,
    phone_number: str,
    scanners: Optional[List[ScannerName]] = None,
    googlecse_max_results: int = 10,
    max_google_links: int = 50,
    timeout: int = 120,
) -> str:
    """
    Run PhoneInfoga scan with selected scanners and return structured JSON.

    PhoneInfoga's CLI does not provide an explicit "enable-only" flag; instead, we
    implement scanner selection by DISABLING all other scanners via `-D/--disable`.

    Args:
        runtime: ToolRuntime (injected by LangChain).
        phone_number: Phone number to scan. May contain spaces and symbols; PhoneInfoga escapes them.
        scanners: Optional list of scanners to run. If None, uses PhoneInfoga defaults.
            Valid: ["local", "numverify", "googlesearch", "googlecse", "ovh"]
        googlecse_max_results: Max results per Google CSE request (1-100, default 10).
        max_google_links: Max google dork links to return for googlesearch (1-500, default 50).
        timeout: Docker execution timeout in seconds (default 120).

    Returns:
        JSON string:
        {
          "status": "success" | "error",
          "number": "...",
          "scanners_requested": ["local", ...] | "default",
          "results": { "local": {...}, "googlesearch": {...}, ... }
        }
    """
    try:
        safe_log_info(
            logger,
            "[phoneinfoga_scan] Starting",
            phone_number=_sanitize_phone_for_logs(phone_number),
            scanners=scanners,
            googlecse_max_results=googlecse_max_results,
            max_google_links=max_google_links,
            timeout=timeout,
        )

        # Resolve keys from ToolRuntime (preferred).
        runtime_cfg = _get_phoneinfoga_config_from_runtime(runtime) if runtime else {}
        resolved_numverify_api_key = runtime_cfg.get("NUMVERIFY_API_KEY")
        resolved_google_api_key = runtime_cfg.get("GOOGLE_API_KEY")
        resolved_googlecse_cx = runtime_cfg.get("GOOGLECSE_CX")

        # Allow runtime to override GOOGLECSE_MAX_RESULTS if caller didn't change the default.
        resolved_googlecse_max_results = googlecse_max_results
        if googlecse_max_results == 10 and runtime_cfg.get("GOOGLECSE_MAX_RESULTS"):
            try:
                resolved_googlecse_max_results = int(str(runtime_cfg.get("GOOGLECSE_MAX_RESULTS")).strip())
            except Exception:
                # Ignore invalid runtime value
                resolved_googlecse_max_results = googlecse_max_results

        # Validate required credentials if user explicitly requests scanners.
        # PhoneInfoga will auto-skip unconfigured scanners, but for agent UX we fail fast
        # when a user intentionally selects a scanner that cannot run.
        if scanners:
            if "numverify" in scanners and not resolved_numverify_api_key:
                error_msg = "NUMVERIFY_API_KEY is required in ToolRuntime when scanners includes 'numverify'"
                safe_log_error(logger, "[phoneinfoga_scan] Validation failed", exc_info=False, error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})
            if "googlecse" in scanners and (not resolved_google_api_key or not resolved_googlecse_cx):
                error_msg = "GOOGLE_API_KEY and GOOGLECSE_CX are required in ToolRuntime when scanners includes 'googlecse'"
                safe_log_error(logger, "[phoneinfoga_scan] Validation failed", exc_info=False, error_msg=error_msg)
                return json.dumps({"status": "error", "message": error_msg})

        return _run_phoneinfoga_scan(
            phone_number=phone_number,
            only_scanners=list(scanners) if scanners else None,
            numverify_api_key=resolved_numverify_api_key,
            google_api_key=resolved_google_api_key,
            googlecse_cx=resolved_googlecse_cx,
            googlecse_max_results=resolved_googlecse_max_results,
            timeout=timeout,
            max_google_links=max_google_links,
        )
    except Exception as e:
        safe_log_error(logger, "[phoneinfoga_scan] Error", exc_info=True, error=str(e))
        return json.dumps({"status": "error", "message": f"PhoneInfoga scan failed: {str(e)}"})


