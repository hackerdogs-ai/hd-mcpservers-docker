"""
Bitbucket Code OSINT (LangChain Tool) - theHarvester-inspired

Reference (theHarvester):
- theHarvester/theHarvester/discovery/bitbucket.py

Notes:
- This is a best-effort port of theHarvester logic.
- Requires API key.
- theHarvester concatenates "fragment" strings from Bitbucket search responses and then
  runs myparser.Parser.emails()/hostnames() over that text.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

import requests
from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.osint.theharvester_parser_utils import extract_emails, extract_hostnames
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info, mask_api_key


logger = setup_logger(__name__, log_file_path="logs/bitbucket_tool.log")
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


def _fragments_from_response(json_data: Any) -> List[str]:
    if not isinstance(json_data, dict):
        return []
    items = json_data.get("items", [])
    if not isinstance(items, list):
        return []
    out: List[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        matches = item.get("text_matches", [])
        if not isinstance(matches, list):
            continue
        for m in matches:
            if isinstance(m, dict) and m.get("fragment") is not None:
                out.append(str(m.get("fragment")))
    return out


@tool
def bitbucket_code_search(
    runtime: ToolRuntime,
    word: str,
    limit: int = 100,
) -> str:
    """
    Bitbucket "code" search (theHarvester-inspired).

    Requires:
      - BITBUCKET_API_KEY

    Args:
      word: theHarvester expects this to include username/repo (e.g., "workspace/repo").
      limit: max fragments to accumulate (best-effort).
    """
    started = time.time()
    w = _normalize_word(word)
    lim = _coerce_int(limit, 100, min_v=1, max_v=500)

    if not w:
        return _json_error("word must be a non-empty string", error_type="validation_error")

    api_key = _get_api_key_from_runtime(runtime, "BITBUCKET_API_KEY")
    if not api_key:
        return _json_error("Missing BITBUCKET_API_KEY", error_type="missing_key", details={"key": "BITBUCKET_API_KEY"})

    timeout_s = _coerce_int(_get_runtime_env(runtime, "BITBUCKET_TIMEOUT"), _DEFAULT_TIMEOUT_S, min_v=3, max_v=120)
    max_retries = _coerce_int(_get_runtime_env(runtime, "BITBUCKET_MAX_RETRIES"), 3, min_v=0, max_v=10)
    retry_wait_s = _coerce_int(_get_runtime_env(runtime, "BITBUCKET_RETRY_WAIT_S"), 60, min_v=0, max_v=600)

    server = "api.bitbucket.org"
    # Mirror theHarvester's base URL (including quotes around the word).
    base_url = f'https://{server}/2.0/repositories/"{w}"/src'
    headers = {"Host": server, "User-agent": "hackerdogs-core/1.0", "Authorization": f"token {api_key}"}

    try:
        safe_log_info(logger, "[bitbucket_code_search] Starting", word=w, limit=lim, timeout_s=timeout_s)

        page = 1
        counter = 0
        retry_count = 0
        total_text = ""
        pages: List[Dict[str, Any]] = []

        while counter <= lim and page != 0:
            url = f"{base_url}&page={page}" if page else base_url
            safe_log_debug(logger, "[bitbucket_code_search] Fetching", page=page, url=url)

            t0 = time.time()
            resp = _SESSION.get(url, headers=headers, timeout=timeout_s)
            elapsed_ms = int((time.time() - t0) * 1000)
            pages.append({"page": page, "url": url, "status_code": resp.status_code, "elapsed_ms": elapsed_ms})

            if resp.status_code == 200:
                retry_count = 0
                try:
                    data = resp.json()
                except Exception:
                    data = {}
                fragments = _fragments_from_response(data)
                # Join with newlines to avoid accidental token "gluing" across fragments
                # (e.g., "...example.com" + "admin@..." => "...example.comadmin@...").
                # This preserves semantics while making downstream parsing stable.
                if fragments:
                    total_text += "\n".join(fragments) + "\n"
                counter += len(fragments)

                # requests parses Link headers into resp.links
                nxt = 0
                links = getattr(resp, "links", {}) or {}
                if isinstance(links, dict) and links.get("next") and isinstance(links["next"], dict) and links["next"].get("url"):
                    # Try to keep advancing; if we can't parse, stop.
                    next_url = str(links["next"]["url"])
                    if "page=" in next_url:
                        try:
                            nxt = int(next_url.split("page=", 1)[1].split("&", 1)[0])
                        except Exception:
                            nxt = 0
                if nxt == page:
                    page = 0
                else:
                    page = nxt
                continue

            if resp.status_code in (429, 403):
                retry_count += 1
                if retry_count > max_retries:
                    page = 0
                    break
                safe_log_info(
                    logger,
                    "[bitbucket_code_search] Rate-limited; backing off",
                    status_code=resp.status_code,
                    retry_count=retry_count,
                    retry_wait_s=retry_wait_s,
                )
                if retry_wait_s > 0:
                    time.sleep(retry_wait_s)
                continue

            # Any other error: stop
            safe_log_error(logger, "[bitbucket_code_search] HTTP error", exc_info=False, status_code=resp.status_code)
            page = 0
            break

        emails = extract_emails(total_text, w)
        hostnames = extract_hostnames(total_text, w)
        elapsed_ms = int((time.time() - started) * 1000)

        safe_log_info(
            logger,
            "[bitbucket_code_search] Completed",
            word=w,
            elapsed_ms=elapsed_ms,
            fragments_seen=counter,
            pages=len(pages),
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
                "fragments_seen": counter,
                "pages": pages,
                "elapsed_ms": elapsed_ms,
            }
        )
    except Exception as e:
        elapsed_ms = int((time.time() - started) * 1000)
        safe_log_error(logger, "[bitbucket_code_search] Unexpected error", exc_info=True, error=str(e), word=w)
        return _json_error(
            f"Bitbucket search failed: {e}",
            error_type="unexpected_error",
            details={"word": w, "elapsed_ms": elapsed_ms},
        )


