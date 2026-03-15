"""
ARIN (American Registry for Internet Numbers) lookup tools (LangChain)

Migrated from SpiderFoot plugin `sfp_arin`:
- Query ARIN Whois REST API for POCs by domain or by person name
- Optionally fetch contact detail URLs returned by ARIN

No API key required.

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

Optional ToolRuntime keys:
1) runtime.state["environment_variables"][<instance>][KEY]
2) runtime.state["environment_variables"][KEY] (flat dict)

Supported keys:
- ARIN_BASE_URL: default "https://whois.arin.net/rest/"
- ARIN_TIMEOUT: integer seconds default 15
- ARIN_USER_AGENT: custom UA (optional)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import quote

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info


logger = setup_logger(__name__, log_file_path="logs/arin_tool.log")
_SESSION = requests.Session()

QueryType = Literal["domain", "name", "contact_url"]

_DEFAULT_BASE_URL = "https://whois.arin.net/rest/"
_DEFAULT_TIMEOUT = 15
_DEFAULT_UA = "Mozilla/5.0 (compatible; hackerdogs-core/1.0; +https://www.arin.net/)"


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


def _coerce_int(value: Optional[str], default: int, *, min_v: int = 1, max_v: int = 120) -> int:
    if value is None:
        return default
    try:
        v = int(value)
        return max(min_v, min(max_v, v))
    except Exception:
        return default


def _request_json(url: str, *, timeout_s: int, ua: str) -> Any:
    resp = _SESSION.get(url, timeout=timeout_s, headers={"User-Agent": ua, "Accept": "application/json"})
    if resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        raise ValueError(f"HTTP {resp.status_code}")
    try:
        return resp.json()
    except Exception:
        # ARIN sometimes returns xml/text depending on endpoints; best-effort
        return {"raw_text": resp.text}


@tool
def arin_lookup(
    runtime: ToolRuntime,
    query_type: QueryType,
    value: str,
    resolve_contacts: bool = False,
    max_contacts: int = 10,
) -> str:
    """
    Query ARIN Whois REST API for POCs by domain, by name, or fetch a contact URL.

    Args:
      query_type: "domain" | "name" | "contact_url"
      value: domain (example.com), name ("First Last"), or full ARIN contact URL
      resolve_contacts: for domain/name queries, optionally fetch contact URLs returned in the response
      max_contacts: limit contact URL fetches
    """
    try:
        safe_log_info(
            logger,
            "[arin_lookup] Starting",
            query_type=query_type,
            value=value,
            resolve_contacts=resolve_contacts,
            max_contacts=max_contacts,
        )
        if query_type not in ("domain", "name", "contact_url"):
            return _json_error("query_type must be one of: domain, name, contact_url", error_type="validation_error")
        if not value or not isinstance(value, str):
            return _json_error("value must be a non-empty string", error_type="validation_error")

        base = _get_runtime_env(runtime, "ARIN_BASE_URL") or _DEFAULT_BASE_URL
        timeout_s = _coerce_int(_get_runtime_env(runtime, "ARIN_TIMEOUT"), _DEFAULT_TIMEOUT, min_v=1, max_v=60)
        ua = _get_runtime_env(runtime, "ARIN_USER_AGENT") or _DEFAULT_UA

        if query_type == "domain":
            url = f"{base.rstrip('/')}/pocs;domain=@{quote(value)}"
        elif query_type == "name":
            parts = value.split()
            if len(parts) < 2:
                return _json_error("name value must include first and last name", error_type="validation_error")
            fname = parts[0].strip(",")
            lname = " ".join(parts[1:]).strip(",")
            url = f"{base.rstrip('/')}/pocs;first={quote(fname)};last={quote(lname)}"
        else:
            url = value

        safe_log_debug(logger, "[arin_lookup] Fetching", url=url, timeout_s=timeout_s)
        data = _request_json(url, timeout_s=timeout_s, ua=ua)
        if data is None:
            return _json_ok({"query_type": query_type, "value": value, "url": url, "result": None})

        contacts: List[Dict[str, Any]] = []
        if resolve_contacts and query_type in ("domain", "name"):
            # Heuristic: find urls under '$' fields in response
            urls: List[str] = []
            try:
                # Common path: data['pocs']['pocRef'] entries with '$' holding url
                pocs = (data.get("pocs") or {}) if isinstance(data, dict) else {}
                refs = pocs.get("pocRef") if isinstance(pocs, dict) else None
                ref_list = []
                if isinstance(refs, dict):
                    ref_list = [refs]
                elif isinstance(refs, list):
                    ref_list = refs
                for r in ref_list:
                    if isinstance(r, dict) and isinstance(r.get("$"), str):
                        urls.append(r["$"])
            except Exception:
                urls = []

            urls = [u for u in urls if u.startswith("http")]
            seen = set()
            unique = []
            for u in urls:
                if u not in seen:
                    seen.add(u)
                    unique.append(u)
            unique = unique[: max(0, min(50, int(max_contacts or 10)))]

            for u in unique:
                try:
                    c = _request_json(u, timeout_s=timeout_s, ua=ua)
                    contacts.append({"url": u, "data": c})
                except Exception as e:
                    contacts.append({"url": u, "error": str(e)})

        return _json_ok(
            {
                "query_type": query_type,
                "value": value,
                "url": url,
                "result": data,
                "resolved_contacts": contacts,
            }
        )

    except requests.exceptions.Timeout as e:
        safe_log_error(logger, "[arin_lookup] Timeout", exc_info=True, error=str(e))
        return _json_error(f"timeout: {e}", error_type="timeout")
    except requests.exceptions.RequestException as e:
        safe_log_error(logger, "[arin_lookup] Request error", exc_info=True, error=str(e))
        return _json_error(f"request_error: {e}", error_type="request_error")
    except ValueError as e:
        safe_log_error(logger, "[arin_lookup] Value error", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="http_error")
    except Exception as e:
        safe_log_error(logger, "[arin_lookup] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}", error_type="unexpected_error")


