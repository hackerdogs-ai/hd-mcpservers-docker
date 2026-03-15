"""
Feed client utilities for IP / CIDR intelligence feeds.

This module provides:
- Loading feed definitions from JSON files in this folder
- Downloading feed contents (requests.Session)
- Parsing feeds into normalized entries (IP / CIDR)
- Fast-ish lookup helpers for IP->range/provider and range->provider
- Timed LRU caching (shared/timed_lru_cache.py) to avoid repeated downloads/parsing

It is intentionally dependency-light (stdlib + requests).
"""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

import ipaddress
import requests

from shared.modules.tools.tool_logging import safe_log_debug, safe_log_error, safe_log_info
from shared.timed_lru_cache import timed_lru_cache


from hd_logging import setup_logger

logger = setup_logger(__name__, log_file_path="logs/feeds_client.log")
_SESSION = requests.Session()

FEEDS_DIR = Path(__file__).resolve().parent


class FeedClientError(RuntimeError):
    """Raised for feed loading/parsing failures."""


@dataclass(frozen=True)
class FeedEntry:
    """
    Normalized feed entry.

    Either `ip` is set (single address) OR `cidr` is set (network).
    """

    source_file: str
    source_key: str
    url: str
    description: str
    provider: Optional[str] = None
    ip: Optional[str] = None
    cidr: Optional[str] = None
    ip_version: Optional[int] = None  # 4 or 6
    meta: Optional[Dict[str, Any]] = None


def _read_json_file(path: Path) -> Dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FeedClientError(f"Feed config not found: {path}") from e
    except json.JSONDecodeError as e:
        raise FeedClientError(f"Invalid JSON in feed config: {path}: {e}") from e
    except Exception as e:
        raise FeedClientError(f"Failed to read feed config: {path}: {e}") from e


def _safe_to_text(resp: requests.Response) -> str:
    # Best-effort decoding; avoid throwing for odd encodings
    try:
        resp.encoding = resp.encoding or "utf-8"
        return resp.text or ""
    except Exception:
        try:
            return (resp.content or b"").decode("utf-8", errors="replace")
        except Exception:
            return ""


def _fetch_url(url: str, *, timeout: int = 30, max_bytes: int = 250_000_000) -> Tuple[int, str, bytes]:
    """
    Fetch URL content safely.

    Returns:
      (status_code, content_type, content_bytes)
    """
    try:
        safe_log_info(logger, "[feeds_client:_fetch_url] Fetching", url=url, timeout=timeout)

        # Local file support for tests / offline usage
        if url.startswith("file://"):
            path = Path(url[len("file://") :])
            content = path.read_bytes()
            if len(content) > max_bytes:
                raise FeedClientError(f"Feed too large ({len(content)} bytes) for {url}")
            return 200, "application/octet-stream", content
        # Also allow plain absolute paths
        if url.startswith("/") and Path(url).exists():
            content = Path(url).read_bytes()
            if len(content) > max_bytes:
                raise FeedClientError(f"Feed too large ({len(content)} bytes) for {url}")
            return 200, "application/octet-stream", content

        resp = _SESSION.get(
            url,
            timeout=timeout,
            headers={
                "User-Agent": "hackerdogs-core/feeds-client (+https://github.com/tejaswiredkar/hackerdogs-core)",
                "Accept": "*/*",
            },
        )
        ct = (resp.headers.get("content-type") or "").split(";")[0].strip().lower()
        content = resp.content or b""
        if len(content) > max_bytes:
            raise FeedClientError(f"Feed too large ({len(content)} bytes) for {url}")
        return resp.status_code, ct, content
    except requests.exceptions.Timeout as e:
        raise FeedClientError(f"timeout fetching {url}: {e}") from e
    except requests.exceptions.RequestException as e:
        raise FeedClientError(f"request error fetching {url}: {e}") from e


# Regexes for extracting IP/CIDR from text/markdown
_RE_IPV4_CIDR = re.compile(r"\b(?:(?:\d{1,3}\.){3}\d{1,3})(?:/\d{1,2})?\b")
_RE_IPV6_CIDR = re.compile(
    r"\b(?:[0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}(?:/\d{1,3})?\b"
)


def _iter_text_tokens(text: str) -> Iterable[str]:
    # Extract v4/v6 candidates; validate later with ipaddress
    for m in _RE_IPV4_CIDR.finditer(text):
        yield m.group(0)
    for m in _RE_IPV6_CIDR.finditer(text):
        yield m.group(0)


def _parse_ip_or_network(token: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """
    Parse token into (ip, cidr, ip_version).
    Returns (ip, None, v) for single address; (None, cidr, v) for network.
    """
    try:
        if "/" in token:
            net = ipaddress.ip_network(token.strip(), strict=False)
            return None, str(net), net.version
        ip = ipaddress.ip_address(token.strip())
        return str(ip), None, ip.version
    except Exception:
        return None, None, None


def _unique_entries(entries: List[FeedEntry]) -> List[FeedEntry]:
    seen = set()
    out: List[FeedEntry] = []
    for e in entries:
        key = (e.source_file, e.source_key, e.ip, e.cidr, e.provider)
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


def _collect_cidrs_recursive(obj: Any) -> List[str]:
    """
    Best-effort CIDR collector for unknown JSON structures.
    This is a fallback and may be noisy, but we validate with ipaddress.
    """
    cidrs: List[str] = []
    if isinstance(obj, str):
        # Common place where CIDRs show up
        for tok in _iter_text_tokens(obj):
            if "/" in tok:
                _, cidr, _ = _parse_ip_or_network(tok)
                if cidr:
                    cidrs.append(cidr)
        return cidrs
    if isinstance(obj, list):
        for item in obj:
            cidrs.extend(_collect_cidrs_recursive(item))
        return cidrs
    if isinstance(obj, dict):
        for v in obj.values():
            cidrs.extend(_collect_cidrs_recursive(v))
        return cidrs
    return cidrs


def _parse_cloud_json(feed_key: str, data: Any) -> List[Tuple[str, int, Dict[str, Any]]]:
    """
    Return list of (cidr, ip_version, meta) for known cloud feeds.
    """
    out: List[Tuple[str, int, Dict[str, Any]]] = []

    try:
        if feed_key == "aws_cloud_ip_ranges" and isinstance(data, dict):
            for p in data.get("prefixes", []) or []:
                if not isinstance(p, dict):
                    continue
                cidr = p.get("ip_prefix")
                if cidr:
                    net = ipaddress.ip_network(str(cidr), strict=False)
                    out.append((str(net), net.version, {"service": p.get("service"), "region": p.get("region")}))
            for p in data.get("ipv6_prefixes", []) or []:
                if not isinstance(p, dict):
                    continue
                cidr = p.get("ipv6_prefix")
                if cidr:
                    net = ipaddress.ip_network(str(cidr), strict=False)
                    out.append((str(net), net.version, {"service": p.get("service"), "region": p.get("region")}))
            return out

        if feed_key == "gcp_cloud_ip_ranges" and isinstance(data, dict):
            for p in data.get("prefixes", []) or []:
                if not isinstance(p, dict):
                    continue
                cidr = p.get("ipv4Prefix") or p.get("ipv6Prefix")
                if not cidr:
                    continue
                net = ipaddress.ip_network(str(cidr), strict=False)
                out.append((str(net), net.version, {"service": p.get("service"), "scope": p.get("scope")}))
            return out

        if feed_key == "azure_ip_ranges" and isinstance(data, dict):
            for v in data.get("values", []) or []:
                if not isinstance(v, dict):
                    continue
                props = v.get("properties") or {}
                if not isinstance(props, dict):
                    continue
                name = v.get("name") or v.get("id")
                region = props.get("region")
                system_service = props.get("systemService")
                for prefix in props.get("addressPrefixes", []) or []:
                    if not prefix:
                        continue
                    net = ipaddress.ip_network(str(prefix), strict=False)
                    out.append(
                        (
                            str(net),
                            net.version,
                            {"name": name, "region": region, "systemService": system_service},
                        )
                    )
            return out

        if feed_key == "all_public_cloud_ip_ranges":
            # Large aggregated json; use recursive CIDR extractor and dedupe.
            cidrs = _collect_cidrs_recursive(data)
            for c in cidrs:
                try:
                    net = ipaddress.ip_network(c, strict=False)
                    out.append((str(net), net.version, {}))
                except Exception:
                    continue
            return out

        if feed_key == "fastly_ip_ranges" and isinstance(data, dict):
            # https://api.fastly.com/public-ip-list
            for c in (data.get("addresses") or []):
                try:
                    net = ipaddress.ip_network(str(c), strict=False)
                    out.append((str(net), net.version, {}))
                except Exception:
                    continue
            for c in (data.get("ipv6_addresses") or []):
                try:
                    net = ipaddress.ip_network(str(c), strict=False)
                    out.append((str(net), net.version, {}))
                except Exception:
                    continue
            return out

        if feed_key == "oracle_cloud_ip_ranges" and isinstance(data, dict):
            # Oracle format: regions[].cidrs[] maybe; do recursive CIDR extraction as safe default
            cidrs = _collect_cidrs_recursive(data)
            for c in cidrs:
                try:
                    net = ipaddress.ip_network(c, strict=False)
                    out.append((str(net), net.version, {}))
                except Exception:
                    continue
            return out

        if feed_key == "github_meta_ip_ranges" and isinstance(data, dict):
            # https://api.github.com/meta contains lists of CIDRs under various keys.
            cidrs = _collect_cidrs_recursive(data)
            for c in cidrs:
                try:
                    net = ipaddress.ip_network(c, strict=False)
                    out.append((str(net), net.version, {}))
                except Exception:
                    continue
            return out

    except Exception as e:
        safe_log_error(logger, "[feeds_client:_parse_cloud_json] parse error", exc_info=True, feed_key=feed_key, error=str(e))

    # Fallback
    cidrs = _collect_cidrs_recursive(data)
    for c in cidrs:
        try:
            net = ipaddress.ip_network(c, strict=False)
            out.append((str(net), net.version, {}))
        except Exception:
            continue
    return out


def _parse_text_ip_list(text: str) -> List[Tuple[str, Optional[str], int, Dict[str, Any]]]:
    """
    Parse a text/markdown document into (ip, label, ip_version, meta).
    """
    out: List[Tuple[str, Optional[str], int, Dict[str, Any]]] = []
    for line in (text or "").splitlines():
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
        # Try to capture a simple "IP - label" style line by extracting first token.
        tokens = list(_iter_text_tokens(line_stripped))
        if not tokens:
            continue
        # Prefer IP over CIDR for name server feeds; if CIDR appears, treat as network.
        for tok in tokens[:3]:
            ip, cidr, ver = _parse_ip_or_network(tok)
            if ip and ver:
                label = None
                # remove the token from the line to keep the rest as label-ish
                rest = line_stripped.replace(tok, "").strip(" -:\t")
                if rest:
                    label = rest[:200]
                out.append((ip, label, ver, {"raw_line": line_stripped[:500]}))
                break
    return out


def _parse_text_cidr_list(text: str) -> List[Tuple[str, int, Dict[str, Any]]]:
    """
    Parse a text document into (cidr, ip_version, meta).

    This is used for providers that publish plaintext CIDR lists (e.g., Cloudflare).
    """
    out: List[Tuple[str, int, Dict[str, Any]]] = []
    for line in (text or "").splitlines():
        line_stripped = line.strip()
        if not line_stripped or line_stripped.startswith("#"):
            continue
        tokens = list(_iter_text_tokens(line_stripped))
        if not tokens:
            continue
        for tok in tokens[:3]:
            if "/" not in tok:
                continue
            _, cidr, ver = _parse_ip_or_network(tok)
            if cidr and ver:
                out.append((cidr, ver, {"raw_line": line_stripped[:500]}))
                break
    return out


def _parse_public_dns_info_csv(content: bytes) -> List[Tuple[str, Optional[str], int, Dict[str, Any]]]:
    """
    Parse https://public-dns.info/nameservers.csv
    CSV format can change; best-effort:
    - first column is usually IP
    - other fields include name/country/reliability
    """
    out: List[Tuple[str, Optional[str], int, Dict[str, Any]]] = []
    try:
        text = content.decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(text))
        for row in reader:
            if not row:
                continue
            candidate = (row[0] or "").strip()
            ip, _, ver = _parse_ip_or_network(candidate)
            if not ip or not ver:
                continue
            label = None
            if len(row) >= 2 and row[1].strip():
                label = row[1].strip()[:200]
            meta: Dict[str, Any] = {}
            if len(row) >= 3:
                meta["row"] = row[:20]
            out.append((ip, label, ver, meta))
        return out
    except Exception as e:
        safe_log_error(logger, "[feeds_client:_parse_public_dns_info_csv] parse error", exc_info=True, error=str(e))
        return []


@timed_lru_cache(seconds=6 * 3600, maxsize=64)
def load_feed_config(feed_config_filename: str) -> Dict[str, Any]:
    """
    Load a feed config JSON file from this directory.
    Cached for 6 hours.
    """
    p = Path(feed_config_filename)
    path = p if p.is_absolute() else (FEEDS_DIR / feed_config_filename)
    safe_log_debug(logger, "[feeds_client:load_feed_config] Loading", path=str(path))
    return _read_json_file(path)


@timed_lru_cache(seconds=6 * 3600, maxsize=256)
def load_feed_entries(feed_config_filename: str, feed_key: str) -> List[FeedEntry]:
    """
    Download + parse a specific feed into normalized FeedEntry objects.
    Cached for 6 hours.
    """
    cfg = load_feed_config(feed_config_filename)
    item = cfg.get(feed_key)
    if not isinstance(item, dict):
        raise FeedClientError(f"Unknown feed key '{feed_key}' in {feed_config_filename}")

    url = str(item.get("url") or "").strip()
    if not url:
        raise FeedClientError(f"Feed '{feed_key}' missing url in {feed_config_filename}")

    description = str(item.get("description") or "").strip()
    download_type = str(item.get("download_type") or item.get("file_type") or "").strip().lower()

    status, ct, content = _fetch_url(url)
    if status >= 400:
        raise FeedClientError(f"HTTP {status} fetching {url}")

    entries: List[FeedEntry] = []

    try:
        if download_type in {"json"} or ct == "application/json":
            data = json.loads(content.decode("utf-8", errors="replace") or "{}")
            # Cloud/datacenter feeds are mostly CIDRs
            cidrs = _parse_cloud_json(feed_key, data)
            provider = _infer_provider(feed_key)
            for cidr, ver, meta in cidrs:
                entries.append(
                    FeedEntry(
                        source_file=feed_config_filename,
                        source_key=feed_key,
                        url=url,
                        description=description,
                        provider=provider,
                        cidr=cidr,
                        ip_version=ver,
                        meta=meta or None,
                    )
                )
        elif download_type in {"txt", "md", "text", "csv"} or ct.startswith("text/"):
            # Some cloud providers publish plaintext CIDR lists (e.g., Cloudflare).
            is_cloud_text_cidr = feed_key in {
                "cloudflare_ip_ranges_v4",
                "cloudflare_ip_ranges_v6",
            }

            if is_cloud_text_cidr:
                provider = _infer_provider(feed_key)
                text = content.decode("utf-8", errors="replace")
                parsed_cidrs = _parse_text_cidr_list(text)
                for cidr, ver, meta in parsed_cidrs:
                    entries.append(
                        FeedEntry(
                            source_file=feed_config_filename,
                            source_key=feed_key,
                            url=url,
                            description=description,
                            provider=provider,
                            cidr=cidr,
                            ip_version=ver,
                            meta=meta or None,
                        )
                    )
            elif feed_key == "public_dns_info_nameservers_csv":
                parsed = _parse_public_dns_info_csv(content)
                for ip, label, ver, meta in parsed:
                    entries.append(
                        FeedEntry(
                            source_file=feed_config_filename,
                            source_key=feed_key,
                            url=url,
                            description=description,
                            provider=None,
                            ip=ip,
                            ip_version=ver,
                            meta={**(meta or {}), **({"label": label} if label else {})} or None,
                        )
                    )
            else:
                parsed = _parse_text_ip_list(content.decode("utf-8", errors="replace"))
                for ip, label, ver, meta in parsed:
                    entries.append(
                        FeedEntry(
                            source_file=feed_config_filename,
                            source_key=feed_key,
                            url=url,
                            description=description,
                            provider=None,
                            ip=ip,
                            ip_version=ver,
                            meta={**(meta or {}), **({"label": label} if label else {})} or None,
                        )
                    )
        else:
            # Best-effort text parsing fallback
            text = content.decode("utf-8", errors="replace")
            parsed = _parse_text_ip_list(text)
            for ip, label, ver, meta in parsed:
                entries.append(
                    FeedEntry(
                        source_file=feed_config_filename,
                        source_key=feed_key,
                        url=url,
                        description=description,
                        ip=ip,
                        ip_version=ver,
                        meta={**(meta or {}), **({"label": label} if label else {})} or None,
                    )
                )
    except Exception as e:
        safe_log_error(logger, "[feeds_client:load_feed_entries] Parse error", exc_info=True, feed_key=feed_key, error=str(e))
        raise FeedClientError(f"Parse error for feed '{feed_key}': {e}") from e

    entries = _unique_entries(entries)
    safe_log_info(
        logger,
        "[feeds_client:load_feed_entries] Loaded entries",
        feed_config=feed_config_filename,
        feed_key=feed_key,
        count=len(entries),
    )
    return entries


def _infer_provider(feed_key: str) -> Optional[str]:
    mapping = {
        "aws_cloud_ip_ranges": "AWS",
        "azure_ip_ranges": "Azure",
        "gcp_cloud_ip_ranges": "GCP",
        "all_public_cloud_ip_ranges": "Cloud",
        "fastly_ip_ranges": "Fastly",
        "cloudflare_ip_ranges_v4": "Cloudflare",
        "cloudflare_ip_ranges_v6": "Cloudflare",
        "oracle_cloud_ip_ranges": "Oracle",
        "github_meta_ip_ranges": "GitHub",
    }
    return mapping.get(feed_key)


@timed_lru_cache(seconds=6 * 3600, maxsize=64)
def load_cloud_network_index(feed_config_filename: str, feed_keys: Optional[Tuple[str, ...]] = None) -> Dict[str, Any]:
    """
    Build an index for cloud/datacenter CIDR feeds in the given config file.

    Returns a dict with:
      - entries: List[FeedEntry] (cidr entries only)
      - buckets_v4: Dict[int, List[int]] mapping first-octet -> list of entry indices
      - buckets_v6: Dict[int, List[int]] mapping first-16bits -> list of entry indices
      - networks: List[ipaddress._BaseNetwork] aligned with entries
    """
    cfg = load_feed_config(feed_config_filename)
    cidr_entries: List[FeedEntry] = []
    networks: List[ipaddress._BaseNetwork] = []

    keys = list(feed_keys) if feed_keys else list(cfg.keys())
    for feed_key in keys:
        try:
            ents = load_feed_entries(feed_config_filename, feed_key)
        except Exception as e:
            safe_log_error(
                logger,
                "[feeds_client:load_cloud_network_index] Failed loading feed",
                exc_info=True,
                feed_key=feed_key,
                error=str(e),
            )
            continue
        for e in ents:
            if not e.cidr:
                continue
            try:
                net = ipaddress.ip_network(e.cidr, strict=False)
                cidr_entries.append(e)
                networks.append(net)
            except Exception:
                continue

    buckets_v4: Dict[int, List[int]] = {i: [] for i in range(256)}
    buckets_v6: Dict[int, List[int]] = {}

    for idx, net in enumerate(networks):
        if net.version == 4:
            start = int(net.network_address) >> 24
            end = int(net.broadcast_address) >> 24
            for b in range(start, end + 1):
                buckets_v4[b].append(idx)
        else:
            start = int(net.network_address) >> (128 - 16)
            end = int(net.broadcast_address) >> (128 - 16)
            for b in range(start, end + 1):
                buckets_v6.setdefault(b, []).append(idx)

    safe_log_info(
        logger,
        "[feeds_client:load_cloud_network_index] Built index",
        feed_config=feed_config_filename,
        cidr_entries=len(cidr_entries),
    )
    return {"entries": cidr_entries, "networks": networks, "buckets_v4": buckets_v4, "buckets_v6": buckets_v6}


def lookup_ip_in_cloud_ranges(
    *,
    feed_config_filename: str,
    ip: str,
    max_results: int = 50,
    feed_keys: Optional[Tuple[str, ...]] = None,
) -> List[Dict[str, Any]]:
    """
    Lookup an IP inside any CIDR from the given cloud feed config.
    """
    ip_obj = ipaddress.ip_address(ip)
    idx = load_cloud_network_index(feed_config_filename, feed_keys)
    entries: List[FeedEntry] = idx["entries"]
    networks: List[ipaddress._BaseNetwork] = idx["networks"]

    candidates: List[int]
    if ip_obj.version == 4:
        b = int(ip_obj) >> 24
        candidates = idx["buckets_v4"].get(b, [])
    else:
        b = int(ip_obj) >> (128 - 16)
        candidates = idx["buckets_v6"].get(b, [])

    matches: List[Tuple[int, int]] = []
    for i in candidates:
        net = networks[i]
        if net.version != ip_obj.version:
            continue
        if ip_obj in net:
            matches.append((net.prefixlen, i))

    # Prefer most-specific networks
    matches.sort(key=lambda t: t[0], reverse=True)

    out: List[Dict[str, Any]] = []
    for _, i in matches[: max_results or 50]:
        e = entries[i]
        out.append(
            {
                "provider": e.provider,
                "cidr": e.cidr,
                "source_key": e.source_key,
                "source_file": e.source_file,
                "description": e.description,
                "meta": e.meta or {},
            }
        )
    return out


def lookup_range_in_cloud_ranges(
    *,
    feed_config_filename: str,
    cidr: str,
    mode: Literal["overlaps", "contains", "contained_by"] = "overlaps",
    max_results: int = 200,
    feed_keys: Optional[Tuple[str, ...]] = None,
) -> List[Dict[str, Any]]:
    """
    Match a CIDR against cloud ranges.
    - overlaps: any overlap
    - contains: cloud range contains the given cidr
    - contained_by: given cidr contains the cloud range
    """
    query = ipaddress.ip_network(cidr, strict=False)
    idx = load_cloud_network_index(feed_config_filename, feed_keys)
    entries: List[FeedEntry] = idx["entries"]
    networks: List[ipaddress._BaseNetwork] = idx["networks"]

    candidates: List[int]
    if query.version == 4:
        start = int(query.network_address) >> 24
        end = int(query.broadcast_address) >> 24
        cand_set = set()
        for b in range(start, end + 1):
            cand_set.update(idx["buckets_v4"].get(b, []))
        candidates = list(cand_set)
    else:
        start = int(query.network_address) >> (128 - 16)
        end = int(query.broadcast_address) >> (128 - 16)
        cand_set = set()
        for b in range(start, end + 1):
            cand_set.update(idx["buckets_v6"].get(b, []))
        candidates = list(cand_set)

    out: List[Dict[str, Any]] = []
    for i in candidates:
        net = networks[i]
        if net.version != query.version:
            continue
        ok = False
        if mode == "overlaps":
            ok = net.overlaps(query)
        elif mode == "contains":
            ok = query.subnet_of(net)
        elif mode == "contained_by":
            ok = net.subnet_of(query)
        if not ok:
            continue
        e = entries[i]
        out.append(
            {
                "provider": e.provider,
                "cidr": e.cidr,
                "source_key": e.source_key,
                "source_file": e.source_file,
                "description": e.description,
                "meta": e.meta or {},
            }
        )
        if len(out) >= (max_results or 200):
            break

    return out


def list_cloud_ranges_for_provider(
    *,
    feed_config_filename: str,
    provider: str,
    ip_version: Optional[int] = None,
    max_results: int = 2000,
    feed_keys: Optional[Tuple[str, ...]] = None,
) -> List[Dict[str, Any]]:
    idx = load_cloud_network_index(feed_config_filename, feed_keys)
    entries: List[FeedEntry] = idx["entries"]
    networks: List[ipaddress._BaseNetwork] = idx["networks"]
    provider_norm = (provider or "").strip().lower()
    out: List[Dict[str, Any]] = []
    for e, net in zip(entries, networks):
        if not e.provider:
            continue
        if e.provider.lower() != provider_norm:
            continue
        if ip_version in (4, 6) and net.version != ip_version:
            continue
        out.append(
            {
                "provider": e.provider,
                "cidr": e.cidr,
                "source_key": e.source_key,
                "source_file": e.source_file,
                "description": e.description,
                "meta": e.meta or {},
            }
        )
        if len(out) >= (max_results or 2000):
            break
    return out


@timed_lru_cache(seconds=6 * 3600, maxsize=64)
def load_nameserver_ip_index(feed_config_filename: str) -> Dict[str, Any]:
    """
    Build a fast lookup dict for resolver IP -> list of (source_key, meta...).
    """
    cfg = load_feed_config(feed_config_filename)
    ip_map: Dict[str, List[FeedEntry]] = {}
    total = 0
    for feed_key in cfg.keys():
        try:
            ents = load_feed_entries(feed_config_filename, feed_key)
        except Exception as e:
            safe_log_error(
                logger,
                "[feeds_client:load_nameserver_ip_index] Failed loading feed",
                exc_info=True,
                feed_key=feed_key,
                error=str(e),
            )
            continue
        for e in ents:
            if not e.ip:
                continue
            ip_map.setdefault(e.ip, []).append(e)
            total += 1
    safe_log_info(logger, "[feeds_client:load_nameserver_ip_index] Built index", entries=total, ips=len(ip_map))
    return {"ip_map": ip_map}


def lookup_nameserver_ip(
    *,
    feed_config_filename: str,
    ip: str,
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    ip_obj = ipaddress.ip_address(ip)  # validate
    idx = load_nameserver_ip_index(feed_config_filename)
    ip_map: Dict[str, List[FeedEntry]] = idx["ip_map"]
    matches = ip_map.get(str(ip_obj), [])[: (max_results or 20)]
    out: List[Dict[str, Any]] = []
    for e in matches:
        out.append(
            {
                "ip": e.ip,
                "source_key": e.source_key,
                "source_file": e.source_file,
                "description": e.description,
                "label": (e.meta or {}).get("label"),
                "meta": e.meta or {},
            }
        )
    return out


def list_nameserver_ips(
    *,
    feed_config_filename: str,
    source_key: Optional[str] = None,
    max_results: int = 2000,
) -> List[Dict[str, Any]]:
    cfg = load_feed_config(feed_config_filename)
    keys = [source_key] if source_key else list(cfg.keys())
    out: List[Dict[str, Any]] = []
    for k in keys:
        try:
            ents = load_feed_entries(feed_config_filename, k)
        except Exception:
            continue
        for e in ents:
            if not e.ip:
                continue
            out.append(
                {
                    "ip": e.ip,
                    "source_key": e.source_key,
                    "source_file": e.source_file,
                    "description": e.description,
                    "label": (e.meta or {}).get("label"),
                }
            )
            if len(out) >= (max_results or 2000):
                return out
    return out


