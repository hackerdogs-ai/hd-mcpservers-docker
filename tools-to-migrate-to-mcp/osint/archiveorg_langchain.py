"""
Archive.org Wayback Machine availability (LangChain Tool)

Migrated from SpiderFoot plugin `sfp_archiveorg`:
- Queries Wayback availability endpoint for a URL at various timestamps (days back)
- Returns closest snapshot URLs found

No API key required.

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

Optional ToolRuntime keys:
1) runtime.state["environment_variables"][<instance>][KEY]
2) runtime.state["environment_variables"][KEY] (flat dict)

Supported keys:
- WAYBACK_AVAILABLE_URL: default "https://archive.org/wayback/available"
- WAYBACK_TIMEOUT: integer seconds default 15
- WAYBACK_USER_AGENT: custom UA (optional)
"""

from __future__ import annotations

import datetime as _dt
import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info


logger = setup_logger(__name__, log_file_path="logs/archiveorg_wayback_tool.log")
_SESSION = requests.Session()

_DEFAULT_AVAILABLE_URL = "https://archive.org/wayback/available"
_DEFAULT_TIMEOUT = 15
_DEFAULT_UA = "Mozilla/5.0 (compatible; hackerdogs-core/1.0; +https://archive.org/)"


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


def _parse_days_back(days_back_csv: str) -> List[int]:
    vals: List[int] = []
    for p in (days_back_csv or "").split(","):
        p = p.strip()
        if not p:
            continue
        try:
            vals.append(int(p))
        except Exception:
            continue
    # Deduplicate + keep stable order
    out: List[int] = []
    for v in vals:
        if v not in out:
            out.append(v)
    return out


@tool
def wayback_available(
    runtime: ToolRuntime,
    url: str,
    days_back_csv: str = "30,60,90",
) -> str:
    """
    Query Archive.org Wayback Machine for available snapshots of a URL at various timestamps.

    Args:
      url: target URL
      days_back_csv: comma-separated days back to query (default: "30,60,90")
    """
    try:
        safe_log_info(logger, "[wayback_available] Starting", url=url, days_back_csv=days_back_csv)
        if not url or not isinstance(url, str):
            return _json_error("url must be a non-empty string", error_type="validation_error")

        base_url = _get_runtime_env(runtime, "WAYBACK_AVAILABLE_URL") or _DEFAULT_AVAILABLE_URL
        timeout_s = _coerce_int(_get_runtime_env(runtime, "WAYBACK_TIMEOUT"), _DEFAULT_TIMEOUT, min_v=1, max_v=60)
        ua = _get_runtime_env(runtime, "WAYBACK_USER_AGENT") or _DEFAULT_UA

        days = _parse_days_back(days_back_csv) or [30, 60, 90]
        snapshots: List[Dict[str, Any]] = []

        for d in days:
            ts = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(days=int(d))).strftime("%Y%m%d")
            qurl = f"{base_url}?{urlencode({'url': url, 'timestamp': ts})}"
            safe_log_debug(logger, "[wayback_available] Fetching", query_url=qurl, timestamp=ts, days_back=d)

            resp = _SESSION.get(qurl, timeout=timeout_s, headers={"User-Agent": ua, "Accept": "application/json,*/*"})
            if resp.status_code == 404:
                continue
            if resp.status_code >= 400:
                snapshots.append({"days_back": d, "timestamp": ts, "error": f"HTTP {resp.status_code}"})
                continue

            try:
                data = resp.json()
            except Exception as e:
                snapshots.append({"days_back": d, "timestamp": ts, "error": f"parse_error: {e}"})
                continue

            closest = ((data.get("archived_snapshots") or {}).get("closest") or {}) if isinstance(data, dict) else {}
            snap_url = closest.get("url") if isinstance(closest, dict) else None
            snapshots.append(
                {
                    "days_back": d,
                    "timestamp": ts,
                    "available": bool(closest.get("available")) if isinstance(closest, dict) else False,
                    "url": snap_url,
                    "status": closest.get("status") if isinstance(closest, dict) else None,
                }
            )

        # Deduplicate snapshot URLs
        seen = set()
        unique_urls: List[str] = []
        for s in snapshots:
            u = s.get("url")
            if isinstance(u, str) and u and u not in seen:
                seen.add(u)
                unique_urls.append(u)

        return _json_ok(
            {
                "url": url,
                "days_back": days,
                "snapshots": snapshots,
                "snapshot_urls": unique_urls,
            }
        )

    except requests.exceptions.Timeout as e:
        safe_log_error(logger, "[wayback_available] Timeout", exc_info=True, error=str(e))
        return _json_error(f"timeout: {e}", error_type="timeout")
    except requests.exceptions.RequestException as e:
        safe_log_error(logger, "[wayback_available] Request error", exc_info=True, error=str(e))
        return _json_error(f"request_error: {e}", error_type="request_error")
    except Exception as e:
        safe_log_error(logger, "[wayback_available] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}", error_type="unexpected_error")


