"""
Cloud / Datacenter IP Range Mapping Tools (LangChain)

These tools use the feed definitions in:
  shared/modules/tools/feeds/cloud_datacenter_feeds.json

They provide:
- IP -> provider/range lookup
- CIDR -> provider/range overlap/containment lookup
- Provider -> list of ranges

Caching:
- Feed downloads/parsing are cached via shared/timed_lru_cache.py in feeds_client.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from langchain.tools import ToolRuntime, tool

from hd_logging import setup_logger
from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info
from shared.modules.tools.feeds.feeds_client import (
    FeedClientError,
    list_cloud_ranges_for_provider,
    lookup_ip_in_cloud_ranges,
    lookup_range_in_cloud_ranges,
    load_feed_config,
)

logger = setup_logger(__name__, log_file_path="logs/cloud_datacenter_feeds.log")

_CLOUD_FEED_FILE = "cloud_datacenter_feeds.json"


def _json_ok(data: Any) -> str:
    return json.dumps({"status": "ok", **(data if isinstance(data, dict) else {"data": data})}, indent=2)


def _json_error(message: str, *, error_type: str = "error", details: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = {"status": "error", "message": message, "error_type": error_type}
    if details:
        payload["details"] = details
    return json.dumps(payload, indent=2)


@tool
def cloud_datacenter_list_feeds(runtime: ToolRuntime) -> str:
    """
    List available cloud/datacenter feeds and their URLs.

    Returns:
      { status: "ok", feeds: { <feed_key>: { url, description, file_type, download_type } } }
    """
    try:
        safe_log_debug(logger, "[cloud_datacenter_list_feeds] Starting")
        cfg = load_feed_config(_CLOUD_FEED_FILE)
        return _json_ok({"feeds": cfg})
    except Exception as e:
        safe_log_error(logger, "[cloud_datacenter_list_feeds] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}")


@tool
def cloud_datacenter_lookup_ip(
    runtime: ToolRuntime,
    ip: str,
    max_results: int = 25,
    feed_keys: Optional[str] = None,
) -> str:
    """
    Lookup a single IP address in known cloud/datacenter CIDR ranges.

    Args:
      ip: IPv4 or IPv6 string.
      max_results: maximum number of matching ranges returned (most-specific first).
    """
    try:
        safe_log_info(logger, "[cloud_datacenter_lookup_ip] Starting", ip=ip, max_results=max_results)
        if not ip or not isinstance(ip, str):
            return _json_error("ip must be a non-empty string", error_type="validation_error")

        keys_tuple = tuple(k.strip() for k in (feed_keys or "").split(",") if k.strip()) or None
        matches = lookup_ip_in_cloud_ranges(
            feed_config_filename=_CLOUD_FEED_FILE,
            ip=ip,
            max_results=max_results,
            feed_keys=keys_tuple,
        )
        return _json_ok({"query": {"ip": ip}, "matches": matches, "match_count": len(matches)})
    except FeedClientError as e:
        safe_log_error(logger, "[cloud_datacenter_lookup_ip] Feed error", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="feed_error")
    except ValueError as e:
        # ipaddress validation error
        safe_log_error(logger, "[cloud_datacenter_lookup_ip] Validation error", exc_info=True, error=str(e))
        return _json_error(f"Invalid IP: {e}", error_type="validation_error")
    except Exception as e:
        safe_log_error(logger, "[cloud_datacenter_lookup_ip] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}")


@tool
def cloud_datacenter_lookup_cidr(
    runtime: ToolRuntime,
    cidr: str,
    mode: str = "overlaps",
    max_results: int = 200,
    feed_keys: Optional[str] = None,
) -> str:
    """
    Lookup a CIDR range against known cloud/datacenter CIDR ranges.

    Args:
      cidr: CIDR string (e.g. "1.2.3.0/24", "2001:db8::/32")
      mode: one of ["overlaps", "contains", "contained_by"]
        - overlaps: any overlap between query CIDR and known ranges
        - contains: known range contains the query CIDR
        - contained_by: query CIDR contains the known range
      max_results: maximum number of matches returned
    """
    try:
        safe_log_info(logger, "[cloud_datacenter_lookup_cidr] Starting", cidr=cidr, mode=mode, max_results=max_results)
        if not cidr or not isinstance(cidr, str):
            return _json_error("cidr must be a non-empty string", error_type="validation_error")
        if mode not in {"overlaps", "contains", "contained_by"}:
            return _json_error("mode must be one of: overlaps, contains, contained_by", error_type="validation_error")

        keys_tuple = tuple(k.strip() for k in (feed_keys or "").split(",") if k.strip()) or None
        matches = lookup_range_in_cloud_ranges(
            feed_config_filename=_CLOUD_FEED_FILE,
            cidr=cidr,
            mode=mode,  # type: ignore[arg-type]
            max_results=max_results,
            feed_keys=keys_tuple,
        )
        return _json_ok({"query": {"cidr": cidr, "mode": mode}, "matches": matches, "match_count": len(matches)})
    except FeedClientError as e:
        safe_log_error(logger, "[cloud_datacenter_lookup_cidr] Feed error", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="feed_error")
    except ValueError as e:
        safe_log_error(logger, "[cloud_datacenter_lookup_cidr] Validation error", exc_info=True, error=str(e))
        return _json_error(f"Invalid CIDR: {e}", error_type="validation_error")
    except Exception as e:
        safe_log_error(logger, "[cloud_datacenter_lookup_cidr] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}")


@tool
def cloud_datacenter_list_ranges_for_provider(
    runtime: ToolRuntime,
    provider: str,
    ip_version: Optional[int] = None,
    max_results: int = 2000,
    feed_keys: Optional[str] = None,
) -> str:
    """
    Return CIDR ranges for a given provider name (e.g., AWS, Azure, GCP, Cloudflare, Fastly, Oracle, GitHub).

    Args:
      provider: provider name (case-insensitive)
      ip_version: optional 4 or 6 filter
      max_results: limit output size
    """
    try:
        safe_log_info(
            logger,
            "[cloud_datacenter_list_ranges_for_provider] Starting",
            provider=provider,
            ip_version=ip_version,
            max_results=max_results,
        )
        if not provider or not isinstance(provider, str):
            return _json_error("provider must be a non-empty string", error_type="validation_error")
        if ip_version is not None and ip_version not in (4, 6):
            return _json_error("ip_version must be 4, 6, or omitted", error_type="validation_error")

        keys_tuple = tuple(k.strip() for k in (feed_keys or "").split(",") if k.strip()) or None
        ranges = list_cloud_ranges_for_provider(
            feed_config_filename=_CLOUD_FEED_FILE,
            provider=provider,
            ip_version=ip_version,
            max_results=max_results,
            feed_keys=keys_tuple,
        )
        return _json_ok(
            {
                "query": {"provider": provider, "ip_version": ip_version},
                "ranges": ranges,
                "range_count": len(ranges),
            }
        )
    except FeedClientError as e:
        safe_log_error(logger, "[cloud_datacenter_list_ranges_for_provider] Feed error", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="feed_error")
    except Exception as e:
        safe_log_error(logger, "[cloud_datacenter_list_ranges_for_provider] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}")


