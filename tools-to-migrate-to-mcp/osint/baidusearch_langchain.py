"""
Baidu Search (LangChain Tool) - theHarvester-style implementation

This tool implements the same *approach* used by theHarvester's Baidu source:
- Build Baidu search URLs with paging (pn=0,10,20,...) and query patterns
- Fetch multiple result pages
- Extract emails and hostnames from the combined HTML (as theHarvester does)

Reference (theHarvester):
- theHarvester/theHarvester/discovery/baidusearch.py
- theHarvester/theHarvester/parsers/myparser.py

Important notes:
- Baidu frequently rate-limits and serves captchas/block pages to scrapers.
  This tool is defensive: it returns structured errors and includes fetch stats.
- No API key is required.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info
from shared.modules.tools.osint.theharvester_parser_utils import extract_emails, extract_hostnames


logger = setup_logger(__name__, log_file_path="logs/baidu_search_tool.log")
_SESSION = requests.Session()

_DEFAULT_TIMEOUT_S = 20
_DEFAULT_UA = "Mozilla/5.0 (compatible; hackerdogs-core/1.0; +https://www.baidu.com/)"


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


def _normalize_word(word: str) -> str:
    w = (word or "").strip()
    if len(w) > 256:
        w = w[:256]
    return w


def _get_runtime_env(runtime: ToolRuntime, key: str) -> Optional[str]:
    """
    Match the repo pattern: search instance dicts first, then flat dict.
    """
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


def _build_baidu_urls(word: str, limit: int) -> List[str]:
    """
    Mirror theHarvester's logic:
      base_url = https://www.baidu.com/s?wd=@<word>&pn=xx&oq=<word>
      pn offsets: 0..limit step 10
    """
    server = "www.baidu.com"
    base_url = f"https://{server}/s?wd=%40{word}&pn=xx&oq={word}"
    urls = [base_url.replace("xx", str(num)) for num in range(0, limit, 10) if num <= limit]
    # Deduplicate while preserving order
    out: List[str] = []
    for u in urls:
        if u not in out:
            out.append(u)
    return out


def _fetch_all(
    urls: List[str],
    *,
    timeout_s: int,
    user_agent: str,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Fetch URLs sequentially (simple + testable) and concatenate responses.
    Returns (combined_html, fetch_stats_per_url).
    """
    combined = []
    stats: List[Dict[str, Any]] = []
    headers = {"User-Agent": user_agent, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}

    for idx, url in enumerate(urls):
        t0 = time.time()
        try:
            safe_log_debug(logger, "[baidu_search_web] Fetching", index=idx, url=url, timeout_s=timeout_s)
            resp = _SESSION.get(url, headers=headers, timeout=timeout_s)
            elapsed_ms = int((time.time() - t0) * 1000)
            content = resp.text or ""
            stats.append(
                {
                    "url": url,
                    "status_code": resp.status_code,
                    "elapsed_ms": elapsed_ms,
                    "content_length": len(content),
                }
            )
            if resp.status_code < 400 and content:
                combined.append(content)
        except requests.exceptions.Timeout as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            safe_log_error(logger, "[baidu_search_web] Timeout fetching", exc_info=True, url=url, elapsed_ms=elapsed_ms, error=str(e))
            stats.append({"url": url, "status_code": None, "elapsed_ms": elapsed_ms, "error": f"timeout: {e}"})
        except requests.exceptions.RequestException as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            safe_log_error(logger, "[baidu_search_web] Request error fetching", exc_info=True, url=url, elapsed_ms=elapsed_ms, error=str(e))
            stats.append({"url": url, "status_code": None, "elapsed_ms": elapsed_ms, "error": f"request_error: {e}"})
        except Exception as e:
            elapsed_ms = int((time.time() - t0) * 1000)
            safe_log_error(logger, "[baidu_search_web] Unexpected error fetching", exc_info=True, url=url, elapsed_ms=elapsed_ms, error=str(e))
            stats.append({"url": url, "status_code": None, "elapsed_ms": elapsed_ms, "error": f"unexpected_error: {e}"})

    return "\n".join(combined), stats


@tool
def baidu_search_web(
    runtime: ToolRuntime,
    word: str,
    limit: int = 50,
) -> str:
    """
    Baidu source equivalent to theHarvester behavior:
    - Fetch Baidu result pages for the given word
    - Extract emails and hostnames from the fetched HTML

    Args:
      runtime: ToolRuntime injected by LangChain.
      word: Company name or domain to search (theHarvester uses the name "word").
      limit: Limit that drives paging offsets (0,10,20,...) up to limit. Default 50.

    Returns:
      JSON with:
        - emails: list of email strings (best-effort, constrained by word domain like theHarvester)
        - hostnames: list of hostnames (best-effort, constrained by word domain like theHarvester)
        - fetched_urls + per-url fetch stats
    """
    started = time.time()
    w = _normalize_word(word)
    lim = _coerce_int(limit, 50, min_v=10, max_v=500)

    if not w:
        return _json_error("word must be a non-empty string", error_type="validation_error")

    timeout_s = _coerce_int(_get_runtime_env(runtime, "BAIDU_TIMEOUT"), _DEFAULT_TIMEOUT_S, min_v=3, max_v=120)
    ua = _get_runtime_env(runtime, "BAIDU_USER_AGENT") or _DEFAULT_UA

    try:
        safe_log_info(logger, "[baidu_search_web] Starting", word=w, limit=lim, timeout_s=timeout_s)

        urls = _build_baidu_urls(w, lim)
        safe_log_debug(
            logger,
            "[baidu_search_web] Built URLs",
            url_count=len(urls),
            first_url=urls[0] if urls else None,
        )

        html, fetch_stats = _fetch_all(urls, timeout_s=timeout_s, user_agent=ua)
        elapsed_ms = int((time.time() - started) * 1000)

        if not html:
            safe_log_error(
                logger,
                "[baidu_search_web] No HTML fetched",
                exc_info=False,
                word=w,
                limit=lim,
                url_count=len(urls),
            )
            return _json_error(
                "No HTML content fetched from Baidu (blocked, captcha, network error, or empty results).",
                error_type="no_content",
                details={
                    "word": w,
                    "limit": lim,
                    "fetched_urls": len(urls),
                    "fetch_stats": fetch_stats[:5],
                    "elapsed_ms": elapsed_ms,
                },
            )

        emails = extract_emails(html, w)
        hostnames = extract_hostnames(html, w)

        # Keep a small preview (avoid returning huge HTML)
        raw_preview = html[:2000] if isinstance(html, str) else None

        safe_log_info(
            logger,
            "[baidu_search_web] Completed",
            word=w,
            elapsed_ms=elapsed_ms,
            emails_count=len(emails),
            hostnames_count=len(hostnames),
            fetched_urls=len(urls),
        )

        return _json_ok(
            {
                "word": w,
                "limit": lim,
                "emails": emails,
                "email_count": len(emails),
                "hostnames": hostnames,
                "hostname_count": len(hostnames),
                "fetched_urls": len(urls),
                "fetch_stats": fetch_stats,
                "raw_preview": raw_preview,
                "elapsed_ms": elapsed_ms,
            }
        )
    except Exception as e:
        elapsed_ms = int((time.time() - started) * 1000)
        safe_log_error(
            logger,
            "[baidu_search_web] Unexpected error",
            exc_info=True,
            error=str(e),
            word=w,
            limit=lim,
            elapsed_ms=elapsed_ms,
        )
        return _json_error(
            f"Baidu search failed: {e}",
            error_type="unexpected_error",
            details={"word": w, "limit": lim, "elapsed_ms": elapsed_ms},
        )


