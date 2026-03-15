"""
Apple iTunes / App Store search (LangChain Tool)

Migrated from SpiderFoot plugin `sfp_apple_itunes`:
- Queries Apple iTunes search API for apps matching a domain (reverse-domain bundle id matching)
- Returns matching apps and useful related URLs

No API key required.

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

Optional ToolRuntime keys:
1) runtime.state["environment_variables"][<instance>][KEY]
2) runtime.state["environment_variables"][KEY] (flat dict)

Supported keys:
- ITUNES_SEARCH_URL: default "https://itunes.apple.com/search"
- ITUNES_TIMEOUT: integer seconds default 15
- ITUNES_SLEEP_SECONDS: float seconds default 0.5 (light rate limiting)
- ITUNES_USER_AGENT: custom UA (optional)
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info


logger = setup_logger(__name__, log_file_path="logs/apple_itunes_tool.log")
_SESSION = requests.Session()

_DEFAULT_SEARCH_URL = "https://itunes.apple.com/search"
_DEFAULT_TIMEOUT = 15
_DEFAULT_SLEEP_SECONDS = 0.5
_DEFAULT_UA = "Mozilla/5.0 (compatible; hackerdogs-core/1.0; +https://itunes.apple.com/)"


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


def _coerce_int(value: Optional[str], default: int, *, min_v: int = 1, max_v: int = 200) -> int:
    if value is None:
        return default
    try:
        v = int(value)
        return max(min_v, min(max_v, v))
    except Exception:
        return default


def _coerce_float(value: Optional[str], default: float, *, min_v: float = 0.0, max_v: float = 5.0) -> float:
    if value is None:
        return default
    try:
        v = float(value)
        return max(min_v, min(max_v, v))
    except Exception:
        return default


def _reverse_domain(domain: str) -> str:
    parts = [p.strip().lower() for p in domain.split(".") if p.strip()]
    return ".".join(reversed(parts))


@tool
def apple_itunes_search_apps_for_domain(
    runtime: ToolRuntime,
    domain: str,
    limit: int = 100,
) -> str:
    """
    Search Apple iTunes for apps whose bundleId matches a domain (reverse-domain naming).

    Example: domain "example.com" -> reverse "com.example"
    Matches:
      - com.example
      - com.example.*
      - *.com.example
      - contains ".com.example."
    """
    try:
        safe_log_info(logger, "[apple_itunes_search_apps_for_domain] Starting", domain=domain, limit=limit)
        if not domain or not isinstance(domain, str) or "." not in domain:
            return _json_error("domain must be a non-empty domain-like string", error_type="validation_error")
        limit = max(1, min(200, int(limit or 100)))

        search_url = _get_runtime_env(runtime, "ITUNES_SEARCH_URL") or _DEFAULT_SEARCH_URL
        timeout_s = _coerce_int(_get_runtime_env(runtime, "ITUNES_TIMEOUT"), _DEFAULT_TIMEOUT, min_v=1, max_v=60)
        sleep_s = _coerce_float(_get_runtime_env(runtime, "ITUNES_SLEEP_SECONDS"), _DEFAULT_SLEEP_SECONDS, min_v=0.0, max_v=2.0)
        ua = _get_runtime_env(runtime, "ITUNES_USER_AGENT") or _DEFAULT_UA

        domain_rev = _reverse_domain(domain)
        params = {
            "media": "software",
            "entity": "software,iPadSoftware,softwareDeveloper",
            "limit": limit,
            "term": domain_rev,
        }

        url = f"{search_url}?{urlencode(params)}"
        safe_log_debug(logger, "[apple_itunes_search_apps_for_domain] Fetching", url=url, timeout_s=timeout_s)

        resp = _SESSION.get(url, timeout=timeout_s, headers={"User-Agent": ua, "Accept": "application/json,*/*"})
        if resp.status_code >= 400:
            return _json_error(f"HTTP {resp.status_code} from iTunes", error_type="http_error", details={"url": url})

        try:
            data = resp.json()
        except Exception as e:
            return _json_error(f"Invalid JSON response: {e}", error_type="parse_error")

        results = data.get("results") or []
        if not isinstance(results, list):
            results = []

        # Light throttling (mirrors SpiderFoot sleep(1) but smaller)
        if sleep_s > 0:
            time.sleep(sleep_s)

        matches: List[Dict[str, Any]] = []
        related_urls: List[str] = []
        related_hosts: List[str] = []

        for r in results:
            if not isinstance(r, dict):
                continue
            bundle_id = r.get("bundleId")
            if not bundle_id or not isinstance(bundle_id, str):
                continue
            b = bundle_id.lower()
            dr = domain_rev.lower()

            if not (b == dr or b.startswith(f"{dr}.") or b.endswith(f".{dr}") or f".{dr}." in b):
                continue

            track_name = r.get("trackName")
            version = r.get("version")
            track_url = r.get("trackViewUrl")
            seller_url = r.get("sellerUrl")

            item = {
                "bundleId": bundle_id,
                "trackName": track_name,
                "version": version,
                "trackViewUrl": track_url,
                "sellerUrl": seller_url,
                "raw": r,
            }
            matches.append(item)

            for u in (track_url, seller_url):
                if isinstance(u, str) and u and u not in related_urls:
                    related_urls.append(u)
                    try:
                        from urllib.parse import urlparse
                        h = urlparse(u).hostname
                        if h and h not in related_hosts:
                            related_hosts.append(h)
                    except Exception:
                        pass

        return _json_ok(
            {
                "domain": domain,
                "domain_reversed": domain_rev,
                "query_url": url,
                "match_count": len(matches),
                "matches": matches[:200],
                "related_urls": related_urls[:200],
                "related_hosts": related_hosts[:200],
            }
        )

    except requests.exceptions.Timeout as e:
        safe_log_error(logger, "[apple_itunes_search_apps_for_domain] Timeout", exc_info=True, error=str(e))
        return _json_error(f"timeout: {e}", error_type="timeout")
    except requests.exceptions.RequestException as e:
        safe_log_error(logger, "[apple_itunes_search_apps_for_domain] Request error", exc_info=True, error=str(e))
        return _json_error(f"request_error: {e}", error_type="request_error")
    except Exception as e:
        safe_log_error(logger, "[apple_itunes_search_apps_for_domain] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}", error_type="unexpected_error")



