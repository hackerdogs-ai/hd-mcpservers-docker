"""
Tools catalog: load from S3 or HTTPS URL, cache in memory with TTL (cachetools).
PRD: configurable TTL, use existing caching library. On load failure retain previous cache.
"""
import json
import re
import threading
from typing import Any, Optional

from cachetools import TTLCache

from app.config import get_settings
from app.exceptions import CatalogLoadError
from app.logging_config import get_logger

logger = get_logger(__name__)

# In-memory cache: key "catalog" -> full catalog dict. Thread lock for safe refresh.
_catalog_cache: Optional[TTLCache[str, dict[str, Any]]] = None
_lock = threading.Lock()


def _fetch_from_url(url: str) -> bytes:
    """Fetch catalog from HTTPS URL."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "ToolsWebService/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        logger.error("catalog_fetch_url_failed", extra={"url": url, "error": str(e)})
        raise CatalogLoadError(f"Failed to fetch catalog from URL: {e}", details={"url": url}) from e


def _fetch_from_s3(uri: str) -> bytes:
    """Fetch catalog from S3. Expects s3://bucket/key."""
    match = re.match(r"s3://([^/]+)/(.+)$", uri.strip())
    if not match:
        raise CatalogLoadError(f"Invalid S3 URI: {uri}", details={"uri": uri})
    bucket, key = match.group(1), match.group(2)
    try:
        import boto3
        client = boto3.client("s3")
        resp = client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read()
    except Exception as e:
        logger.error("catalog_fetch_s3_failed", extra={"bucket": bucket, "key": key, "error": str(e)})
        raise CatalogLoadError(f"Failed to fetch catalog from S3: {e}", details={"bucket": bucket, "key": key}) from e


def _load_catalog_fresh() -> dict[str, Any]:
    """Load catalog from configured source (S3 or URL). Raises CatalogLoadError on failure."""
    settings = get_settings()
    source = settings.get_catalog_source()
    if not source:
        raise CatalogLoadError(
            "No catalog source configured. Set TOOLS_CATALOG_S3_URI or TOOLS_CATALOG_URL.",
            details={},
        )
    raw: bytes
    if source.strip().lower().startswith("s3://"):
        raw = _fetch_from_s3(source)
    else:
        raw = _fetch_from_url(source)
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError as e:
        logger.error("catalog_json_invalid", extra={"error": str(e)})
        raise CatalogLoadError(f"Catalog JSON invalid: {e}", details={}) from e
    if not isinstance(data, dict) or "tools" not in data:
        raise CatalogLoadError("Catalog must be a JSON object with a 'tools' array.", details={})
    if not isinstance(data["tools"], list):
        raise CatalogLoadError("Catalog 'tools' must be an array.", details={})
    logger.info("catalog_loaded", extra={"tool_count": len(data["tools"])})
    return data


def _get_cache() -> TTLCache[str, dict[str, Any]]:
    global _catalog_cache
    if _catalog_cache is None:
        settings = get_settings()
        _catalog_cache = TTLCache(
            maxsize=settings.tools_cache_maxsize or 10,
            ttl=settings.tools_cache_ttl_seconds,
        )
    return _catalog_cache


def get_catalog() -> dict[str, Any]:
    """
    Return cached catalog or load from storage. Uses cachetools TTL.
    On load failure: if we have a previous cache, return it and log error (resiliency).
    """
    cache = _get_cache()
    with _lock:
        try:
            cat = cache.get("catalog")
            if cat is not None:
                return cat
        except Exception:
            pass

        try:
            cat = _load_catalog_fresh()
            cache["catalog"] = cat
            return cat
        except CatalogLoadError:
            try:
                stale = cache.get("catalog")
                if stale is not None:
                    logger.warning("catalog_load_failed_using_stale", extra={"error": "catalog_load_error"})
                    return stale
            except Exception:
                pass
            raise
        except Exception as e:
            logger.exception("catalog_load_unexpected_error", extra={"error": str(e)})
            try:
                stale = cache.get("catalog")
                if stale is not None:
                    logger.warning("catalog_load_failed_using_stale", extra={"error": str(e)})
                    return stale
            except Exception:
                pass
            raise CatalogLoadError(f"Catalog load failed: {e}", details={}) from e


def get_tool_by_id(tool_id: str) -> Optional[dict[str, Any]]:
    """Return tool dict by id or None."""
    catalog = get_catalog()
    tools = catalog.get("tools") or []
    for t in tools:
        if t.get("id") == tool_id:
            return t
    return None


def get_first_mcp_server_config(tool: dict[str, Any]) -> Optional[tuple[str, dict[str, Any]]]:
    """Return (server_name, server_config) from tool['configuration']['mcpServers'] or None."""
    config = tool.get("configuration") or {}
    servers = config.get("mcpServers") or {}
    if not servers:
        return None
    name = next(iter(servers))
    return name, servers[name]
