"""
Ahmia (Tor search engine) query tool (LangChain)

Migrated from SpiderFoot plugin `sfp_ahmia`:
- Searches Ahmia for a query string
- Extracts result URLs from the HTML
- Optionally fetches page content (best-effort; onion sites often require Tor)

No API key required.

================================================================================
ENVIRONMENT VARIABLES AND CONFIGURATION
================================================================================

Optional ToolRuntime keys:
1) runtime.state["environment_variables"][<instance>][KEY]
2) runtime.state["environment_variables"][KEY] (flat dict)

Supported keys:
- AHMIA_BASE_URL: default "https://ahmia.fi"
- AHMIA_TIMEOUT: integer seconds default 15
- AHMIA_USER_AGENT: custom UA (optional)
- AHMIA_TOR_PROXY: optional proxy URL (e.g. "socks5h://127.0.0.1:9050")
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info


logger = setup_logger(__name__, log_file_path="logs/ahmia_tool.log")
_SESSION = requests.Session()

_DEFAULT_BASE_URL = "https://ahmia.fi"
_DEFAULT_TIMEOUT = 15
_DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; hackerdogs-core/1.0; +https://ahmia.fi/)"


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


def _build_proxies(proxy_url: Optional[str]) -> Optional[Dict[str, str]]:
    if not proxy_url:
        return None
    # requests expects scheme://host:port
    return {"http": proxy_url, "https": proxy_url}


_RE_REDIRECT = re.compile(r"redirect_url=([^\"&]+)")


@tool
def ahmia_search(
    runtime: ToolRuntime,
    query: str,
    max_results: int = 50,
    only_onion: bool = True,
    fetch_content: bool = False,
) -> str:
    """
    Search Ahmia for a query and return result URLs.

    Args:
      query: search string
      max_results: cap returned results
      only_onion: keep only .onion results (matches SpiderFoot behavior)
      fetch_content: best-effort fetch of result pages; onion sites often require Tor/proxy
    """
    try:
        safe_log_info(logger, "[ahmia_search] Starting", query=query, max_results=max_results, only_onion=only_onion, fetch_content=fetch_content)
        if not query or not isinstance(query, str):
            return _json_error("query must be a non-empty string", error_type="validation_error")
        max_results = max(1, min(200, int(max_results or 50)))

        base_url = _get_runtime_env(runtime, "AHMIA_BASE_URL") or _DEFAULT_BASE_URL
        timeout_s = _coerce_int(_get_runtime_env(runtime, "AHMIA_TIMEOUT"), _DEFAULT_TIMEOUT, min_v=1, max_v=60)
        user_agent = _get_runtime_env(runtime, "AHMIA_USER_AGENT") or _DEFAULT_USER_AGENT
        tor_proxy = _get_runtime_env(runtime, "AHMIA_TOR_PROXY")

        search_url = f"{base_url.rstrip('/')}/search/?{urlencode({'q': query})}"
        safe_log_debug(logger, "[ahmia_search] Fetching search results", search_url=search_url, timeout_s=timeout_s)

        resp = _SESSION.get(
            search_url,
            timeout=timeout_s,
            headers={"User-Agent": user_agent, "Accept": "text/html,*/*"},
            proxies=_build_proxies(tor_proxy),
        )
        if resp.status_code >= 400:
            return _json_error(f"HTTP {resp.status_code} from Ahmia", error_type="http_error", details={"url": search_url})

        html = resp.text or ""
        links = _RE_REDIRECT.findall(html)
        # URL decode-ish: Ahmia uses standard URL encoding in redirect_url parameter
        from urllib.parse import unquote

        results: List[str] = []
        for raw in links:
            u = unquote(raw)
            if only_onion and not u.endswith(".onion") and ".onion/" not in u and ".onion?" not in u:
                continue
            if u not in results:
                results.append(u)
            if len(results) >= max_results:
                break

        fetched: List[Dict[str, Any]] = []
        if fetch_content and results:
            for u in results[: min(10, len(results))]:
                try:
                    r = _SESSION.get(
                        u,
                        timeout=timeout_s,
                        headers={"User-Agent": user_agent, "Accept": "text/html,*/*"},
                        proxies=_build_proxies(tor_proxy),
                        verify=False,
                    )
                    fetched.append({"url": u, "status_code": r.status_code, "content_len": len(r.content or b"")})
                except requests.exceptions.RequestException as e:
                    fetched.append({"url": u, "error": str(e)})

        return _json_ok(
            {
                "query": query,
                "search_url": search_url,
                "only_onion": only_onion,
                "max_results": max_results,
                "results": results,
                "result_count": len(results),
                "fetched_samples": fetched,
            }
        )

    except requests.exceptions.Timeout as e:
        safe_log_error(logger, "[ahmia_search] Timeout", exc_info=True, error=str(e))
        return _json_error(f"timeout: {e}", error_type="timeout")
    except requests.exceptions.RequestException as e:
        safe_log_error(logger, "[ahmia_search] Request error", exc_info=True, error=str(e))
        return _json_error(f"request_error: {e}", error_type="request_error")
    except Exception as e:
        safe_log_error(logger, "[ahmia_search] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}", error_type="unexpected_error")



