"""
AdBlock / EasyList URL Blocking Check (LangChain Tool)

Migrated conceptually from SpiderFoot plugin `sfp_adblock`:
- Downloads an AdBlock Plus compatible filter list (EasyList by default)
- Caches list parsing for performance
- Checks whether a given URL/resource would be blocked, given simple context flags

No API keys required.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Literal, Optional

import requests
from langchain.tools import ToolRuntime, tool
from pathlib import Path

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info
from shared.timed_lru_cache import timed_lru_cache


logger = setup_logger(__name__, log_file_path="logs/adblock_langchain_tool.log")
_SESSION = requests.Session()

_DEFAULT_BLOCKLIST_URL = "https://easylist-downloads.adblockplus.org/easylist.txt"
_DEFAULT_TIMEOUT_SECONDS = 30
_BLOCKLIST_MAX_BYTES = 15 * 1024 * 1024

# Keep this aligned with SpiderFoot default (24h)
_CACHE_SECONDS = 24 * 3600

ResourceType = Literal["page", "script", "image", "xhr", "stylesheet", "other"]


def _json_ok(data: Dict[str, Any]) -> str:
    return json.dumps({"status": "ok", **data}, indent=2)


def _json_error(message: str, *, error_type: str = "error", details: Optional[Dict[str, Any]] = None) -> str:
    out: Dict[str, Any] = {"status": "error", "message": message, "error_type": error_type}
    if details:
        out["details"] = details
    return json.dumps(out, indent=2)


def _resource_flags(resource_type: ResourceType, third_party: bool) -> Dict[str, Any]:
    """
    Map a simple resource_type into adblockparser option flags.
    """
    flags: Dict[str, Any] = {"third-party": bool(third_party)}
    if resource_type == "script":
        flags["script"] = True
    elif resource_type == "image":
        flags["image"] = True
    elif resource_type == "xhr":
        # adblockparser uses 'xmlhttprequest'
        flags["xmlhttprequest"] = True
    elif resource_type == "stylesheet":
        flags["stylesheet"] = True
    # page/other: no additional flags
    return flags


def _fetch_blocklist_text(url: str, timeout: int) -> str:
    try:
        safe_log_info(logger, "[_fetch_blocklist_text] Fetching blocklist", url=url, timeout=timeout)
        # Support local file:// URLs for tests/offline use
        if url.startswith("file://"):
            p = url[len("file://") :]
            data = bytes(Path(p).read_bytes())  # type: ignore[name-defined]
            if len(data) > _BLOCKLIST_MAX_BYTES:
                raise ValueError(f"Blocklist too large ({len(data)} bytes)")
            return data.decode("utf-8", errors="replace")

        resp = _SESSION.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "hackerdogs-core/adblock-tool",
                "Accept": "text/plain,*/*",
            },
        )
        if resp.status_code >= 400:
            raise ValueError(f"HTTP {resp.status_code} while fetching blocklist")

        content = resp.content or b""
        if len(content) > _BLOCKLIST_MAX_BYTES:
            raise ValueError(f"Blocklist too large ({len(content)} bytes)")

        # Best-effort decode
        try:
            resp.encoding = resp.encoding or "utf-8"
            return resp.text or ""
        except Exception:
            return content.decode("utf-8", errors="replace")

    except requests.exceptions.Timeout as e:
        raise TimeoutError(str(e)) from e
    except requests.exceptions.RequestException as e:
        raise ConnectionError(str(e)) from e


@timed_lru_cache(seconds=_CACHE_SECONDS, maxsize=32)
def _cached_blocklist_lines(blocklist_url: str) -> list[str]:
    """
    Download and parse blocklist into lines. Cached for 24h.
    """
    text = _fetch_blocklist_text(blocklist_url, timeout=_DEFAULT_TIMEOUT_SECONDS)
    # Keep original semantics: split into lines
    return (text or "").splitlines()


@timed_lru_cache(seconds=_CACHE_SECONDS, maxsize=32)
def _cached_rules(blocklist_url: str):
    """
    Parse cached lines into AdblockRules. Cached for 24h.
    """
    try:
        import adblockparser
    except Exception as e:  # pragma: no cover
        raise ImportError("adblockparser is not installed. Add adblockparser==0.7 to requirements.") from e

    lines = _cached_blocklist_lines(blocklist_url)
    # AdblockRules may raise AdblockParsingError
    return adblockparser.AdblockRules(lines)


@tool
def adblock_check_url(
    runtime: ToolRuntime,
    url: str,
    third_party: bool = False,
    resource_type: ResourceType = "page",
    blocklist_url: str = _DEFAULT_BLOCKLIST_URL,
    timeout_seconds: int = _DEFAULT_TIMEOUT_SECONDS,
) -> str:
    """
    Check if a URL would be blocked by AdBlock Plus compatible rules (EasyList by default).

    Args:
      url: URL to check
      third_party: whether the resource is considered third-party
      resource_type: context hint (page/script/image/xhr/stylesheet/other)
      blocklist_url: ABP-compatible blocklist URL (default: EasyList)
      timeout_seconds: HTTP timeout for fetching blocklist (used on cache miss)
    """
    try:
        safe_log_info(
            logger,
            "[adblock_check_url] Starting",
            url=url,
            third_party=third_party,
            resource_type=resource_type,
            blocklist_url=blocklist_url,
            timeout_seconds=timeout_seconds,
        )

        if not url or not isinstance(url, str):
            return _json_error("url must be a non-empty string", error_type="validation_error")
        if not blocklist_url or not isinstance(blocklist_url, str):
            return _json_error("blocklist_url must be a non-empty string", error_type="validation_error")
        if timeout_seconds <= 0 or timeout_seconds > 120:
            return _json_error("timeout_seconds must be between 1 and 120", error_type="validation_error")

        # NOTE: the cached downloader uses a fixed default timeout; enforce caller timeout on direct fetch
        # by priming cache when needed.
        if timeout_seconds != _DEFAULT_TIMEOUT_SECONDS:
            # If caller wants a different timeout, do a one-off fetch and parse without caching.
            safe_log_debug(logger, "[adblock_check_url] Using non-default timeout (no-cache path)", timeout_seconds=timeout_seconds)
            lines = (_fetch_blocklist_text(blocklist_url, timeout=timeout_seconds) or "").splitlines()
            import adblockparser
            rules = adblockparser.AdblockRules(lines)
        else:
            rules = _cached_rules(blocklist_url)

        opts = _resource_flags(resource_type, third_party)
        blocked = bool(rules.should_block(url, opts))

        return _json_ok(
            {
                "url": url,
                "blocked": blocked,
                "context": {"third_party": bool(third_party), "resource_type": resource_type, "options": opts},
                "blocklist": {"url": blocklist_url, "cache_ttl_hours": int(_CACHE_SECONDS / 3600)},
            }
        )

    except ImportError as e:
        safe_log_error(logger, "[adblock_check_url] Missing dependency", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="dependency_error")
    except TimeoutError as e:
        safe_log_error(logger, "[adblock_check_url] Timeout fetching blocklist", exc_info=True, error=str(e))
        return _json_error(f"timeout fetching blocklist: {e}", error_type="timeout")
    except ConnectionError as e:
        safe_log_error(logger, "[adblock_check_url] Request error fetching blocklist", exc_info=True, error=str(e))
        return _json_error(f"request error fetching blocklist: {e}", error_type="request_error")
    except ValueError as e:
        safe_log_error(logger, "[adblock_check_url] Validation/value error", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="validation_error")
    except Exception as e:
        # Includes adblockparser.AdblockParsingError and any unexpected issues
        safe_log_error(logger, "[adblock_check_url] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}", error_type="unexpected_error")


