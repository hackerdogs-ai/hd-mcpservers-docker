"""
Name Server / Public DNS Resolver Mapping Tools (LangChain)

These tools use the feed definitions in:
  shared/modules/tools/feeds/name_server_feeds.json

They provide:
- IP -> which feed(s) contain it (and any label found on the line/row)
- List resolver IPs (optionally filtered by feed key)

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
    list_nameserver_ips,
    load_feed_config,
    lookup_nameserver_ip,
)

logger = setup_logger(__name__, log_file_path="logs/name_server_feeds.log")

_NS_FEED_FILE = "name_server_feeds.json"


def _json_ok(data: Any) -> str:
    return json.dumps({"status": "ok", **(data if isinstance(data, dict) else {"data": data})}, indent=2)


def _json_error(message: str, *, error_type: str = "error", details: Optional[Dict[str, Any]] = None) -> str:
    payload: Dict[str, Any] = {"status": "error", "message": message, "error_type": error_type}
    if details:
        payload["details"] = details
    return json.dumps(payload, indent=2)


@tool
def name_server_list_feeds(runtime: ToolRuntime) -> str:
    """
    List available name server / public DNS resolver feeds and their URLs.
    """
    try:
        safe_log_debug(logger, "[name_server_list_feeds] Starting")
        cfg = load_feed_config(_NS_FEED_FILE)
        return _json_ok({"feeds": cfg})
    except Exception as e:
        safe_log_error(logger, "[name_server_list_feeds] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}")


@tool
def name_server_lookup_ip(
    runtime: ToolRuntime,
    ip: str,
    max_results: int = 20,
) -> str:
    """
    Lookup whether an IP address is present in any configured public resolver/name-server lists.

    Args:
      ip: IPv4 or IPv6 string.
      max_results: maximum number of matching records returned.
    """
    try:
        safe_log_info(logger, "[name_server_lookup_ip] Starting", ip=ip, max_results=max_results)
        if not ip or not isinstance(ip, str):
            return _json_error("ip must be a non-empty string", error_type="validation_error")

        matches = lookup_nameserver_ip(feed_config_filename=_NS_FEED_FILE, ip=ip, max_results=max_results)
        return _json_ok({"query": {"ip": ip}, "matches": matches, "match_count": len(matches)})
    except FeedClientError as e:
        safe_log_error(logger, "[name_server_lookup_ip] Feed error", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="feed_error")
    except ValueError as e:
        safe_log_error(logger, "[name_server_lookup_ip] Validation error", exc_info=True, error=str(e))
        return _json_error(f"Invalid IP: {e}", error_type="validation_error")
    except Exception as e:
        safe_log_error(logger, "[name_server_lookup_ip] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}")


@tool
def name_server_list_ips(
    runtime: ToolRuntime,
    source_key: Optional[str] = None,
    max_results: int = 2000,
) -> str:
    """
    List resolver IPs from all feeds or from a single feed key.

    Args:
      source_key: optional feed key (e.g., "dnscrypt_public_resolvers")
      max_results: limit output size
    """
    try:
        safe_log_info(logger, "[name_server_list_ips] Starting", source_key=source_key, max_results=max_results)
        ips = list_nameserver_ips(feed_config_filename=_NS_FEED_FILE, source_key=source_key, max_results=max_results)
        return _json_ok(
            {
                "query": {"source_key": source_key},
                "ips": ips,
                "ip_count": len(ips),
            }
        )
    except FeedClientError as e:
        safe_log_error(logger, "[name_server_list_ips] Feed error", exc_info=True, error=str(e))
        return _json_error(str(e), error_type="feed_error")
    except Exception as e:
        safe_log_error(logger, "[name_server_list_ips] Unexpected error", exc_info=True, error=str(e))
        return _json_error(f"Unexpected error: {e}")


