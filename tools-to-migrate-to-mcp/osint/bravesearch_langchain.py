"""
Brave Search OSINT (LangChain Tool) - theHarvester-inspired

Reference (theHarvester):
- theHarvester/theHarvester/discovery/bravesearch.py

theHarvester behavior:
- Requires API key (X-Subscription-Token)
- Queries:
  - "<word>" (exact-ish)
  - site:<word>
- Paginates with offset in steps of 20 (max 5 pages)
- Aggregates result text and extracts emails/hostnames via myparser.Parser
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.osint.theharvester_parser_utils import extract_emails, extract_hostnames
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info, mask_api_key


logger = setup_logger(__name__, log_file_path="logs/bravesearch_tool.log")
_SESSION = requests.Session()

_DEFAULT_TIMEOUT_S = 20


def _json_ok(payload: Dict[str, Any]) -> str:
    return json.dumps({"status": "success", **payload}, ensure_ascii=False, indent=2, default=str)


def _json_error(
    message: str,
    *,
    error_type: str = "error",
    details: Optional[Dict[str, Any]] = None,
) -> str:
    out: Dict[str, Any] = {"status": "error", "message": message, "error_type": error_type}
    if details:
        out["details"] = details
    return json.dumps(out, ensure_ascii=False, indent=2, default=str)


def _coerce_int(value: Any, default: int, *, min_v: int, max_v: int) -> int:
    try:
        v = int(value)
        return max(min_v, min(max_v, v))
    except Exception:
        return default


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


def _get_api_key_from_runtime(runtime: ToolRuntime, key_name: str) -> Optional[str]:
    if runtime and getattr(runtime, "state", None):
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


def _normalize_word(word: str) -> str:
    w = (word or "").strip()
    if len(w) > 256:
        w = w[:256]
    return w


def _build_brave_url(base: str, params: Dict[str, Any]) -> str:
    param_string = "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
    return f"{base}?{param_string}"


@tool
def bravesearch_domain_search(
    runtime: ToolRuntime,
    word: str,
    limit: int = 100,
) -> str:
    """
    Brave Search API (theHarvester-style) to collect text and extract emails/hostnames.

    Requires:
      - BRAVE_API_KEY
        (sent as header X-Subscription-Token)
    """
    started = time.time()
    w = _normalize_word(word)
    lim = _coerce_int(limit, 100, min_v=1, max_v=500)

    if not w:
        return _json_error("word must be a non-empty string", error_type="validation_error")

    api_key = _get_api_key_from_runtime(runtime, "BRAVE_API_KEY")
    if not api_key:
        return _json_error("Missing BRAVE_API_KEY", error_type="missing_key", details={"key": "BRAVE_API_KEY"})

    timeout_s = _coerce_int(_get_runtime_env(runtime, "BRAVE_TIMEOUT"), _DEFAULT_TIMEOUT_S, min_v=3, max_v=120)
    max_pages = _coerce_int(_get_runtime_env(runtime, "BRAVE_MAX_PAGES"), 5, min_v=1, max_v=5)

    base_url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": api_key}

    try:
        safe_log_info(logger, "[bravesearch_domain_search] Starting", word=w, limit=lim, timeout_s=timeout_s, max_pages=max_pages)

        queries = [f"\"{w}\"", f"site:{w}"]
        total_text = ""
        fetched = 0
        page_requests: List[Dict[str, Any]] = []

        for q in queries:
            # 20 results per page, limit max 5 pages like theHarvester
            pages = min((lim // 20) + 1, max_pages)
            for offset in range(0, pages * 20, 20):
                if fetched >= lim:
                    break
                params = {
                    "q": q,
                    "count": min(20, lim - fetched),
                    "offset": offset,
                    "safesearch": "off",
                    "freshness": "all",
                    "extra_snippets": "true",
                    "text_decorations": "true",
                    "spellcheck": "true",
                }
                url = _build_brave_url(base_url, params)
                safe_log_debug(logger, "[bravesearch_domain_search] Fetching", query=q, offset=offset, url=url)

                t0 = time.time()
                resp = _SESSION.get(url, headers=headers, timeout=timeout_s)
                elapsed_ms = int((time.time() - t0) * 1000)
                page_requests.append({"query": q, "offset": offset, "status_code": resp.status_code, "elapsed_ms": elapsed_ms})

                data: Any
                try:
                    data = resp.json()
                except Exception:
                    data = {"raw_text": resp.text}

                if resp.status_code >= 400:
                    # Stop on hard errors; let caller see partials if any.
                    safe_log_error(
                        logger,
                        "[bravesearch_domain_search] HTTP error",
                        exc_info=False,
                        status_code=resp.status_code,
                        query=q,
                        offset=offset,
                    )
                    break

                results = (((data or {}).get("web") or {}).get("results") or []) if isinstance(data, dict) else []
                if not results:
                    break

                for r in results:
                    if not isinstance(r, dict):
                        continue
                    result_text = f'{r.get("title", "")} {r.get("description", "")}'
                    extra = r.get("extra_snippets")
                    if isinstance(extra, list):
                        for s in extra:
                            result_text += f" {s}"
                    result_text += f' {r.get("url", "")}'
                    total_text += result_text + "\n"
                fetched += len(results)

        emails = extract_emails(total_text, w)
        hostnames = extract_hostnames(total_text, w)
        elapsed_ms = int((time.time() - started) * 1000)

        safe_log_info(
            logger,
            "[bravesearch_domain_search] Completed",
            word=w,
            elapsed_ms=elapsed_ms,
            fetched_results=fetched,
            emails_count=len(emails),
            hostnames_count=len(hostnames),
        )

        return _json_ok(
            {
                "word": w,
                "limit": lim,
                "emails": emails,
                "email_count": len(emails),
                "hostnames": hostnames,
                "hostname_count": len(hostnames),
                "fetched_results": fetched,
                "requests": page_requests,
                "elapsed_ms": elapsed_ms,
            }
        )
    except Exception as e:
        elapsed_ms = int((time.time() - started) * 1000)
        safe_log_error(logger, "[bravesearch_domain_search] Unexpected error", exc_info=True, error=str(e), word=w)
        return _json_error(
            f"Brave Search failed: {e}",
            error_type="unexpected_error",
            details={"word": w, "elapsed_ms": elapsed_ms},
        )


