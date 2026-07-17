"""
Redis Stack (RediSearch) vector index for MCP Farm tool routing.

This talks to the shared ``hd-redis`` instance but keeps everything under a
farm-specific key prefix (default ``mcpfarm:v1``) and a dedicated index
(``mcpfarm:idx``) so it never collides with other services sharing the box.

Docs are stored as Redis HASHes:

    key:   mcpfarm:v1:doc:{server}:{kind}:{suffix}
    fields: text, server, tool, doc_type, category, status, display_name,
            chunk_index, embedding (FLOAT32 blob)

We use raw ``FT.CREATE`` / ``FT.SEARCH`` commands via ``execute_command`` to stay
independent of redis-py helper-API differences across versions.
"""
from __future__ import annotations

import logging
import os
import struct
from typing import Dict, List, Optional

import redis.asyncio as redis

from embeddings import VECTOR_DIM

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://hd-redis:6379")
PREFIX = os.environ.get("MCPFARM_VECTOR_PREFIX", "mcpfarm:v1")
DOC_PREFIX = f"{PREFIX}:doc:"
INDEX_NAME = os.environ.get("MCPFARM_VECTOR_INDEX", "mcpfarm:idx")

DISTANCE_METRIC = "COSINE"

_client: Optional[redis.Redis] = None

_TAG_SPECIAL = set(",.<>{}[]\"'`:;!@#$%^&*()-+=~/| \\\n\t")


def get_client() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL, decode_responses=False)
        # redis-py >= 8 registers a FT.SEARCH response callback that assumes it
        # was invoked through the ``.ft().search()`` helper and raises KeyError
        # when called via raw ``execute_command``. We parse the RESP array
        # ourselves, so replace that callback with a passthrough for stability
        # across redis-py versions.
        try:
            _client.set_response_callback("FT.SEARCH", lambda response, **_: response)
        except Exception:  # noqa: BLE001 - older clients have no such callback
            pass
    return _client


def escape_tag(value: str) -> str:
    """Escape RediSearch TAG special characters (server names contain '-')."""
    return "".join("\\" + c if c in _TAG_SPECIAL else c for c in (value or ""))


def to_vector_bytes(vec: List[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _decode(v):
    return v.decode("utf-8", "replace") if isinstance(v, (bytes, bytearray)) else v


async def index_exists() -> bool:
    try:
        await get_client().execute_command("FT.INFO", INDEX_NAME)
        return True
    except Exception:
        return False


async def ensure_index(dim: int = VECTOR_DIM) -> bool:
    """Create the index if it does not already exist. Returns True if created."""
    if await index_exists():
        return False
    await get_client().execute_command(
        "FT.CREATE", INDEX_NAME,
        "ON", "HASH",
        "PREFIX", "1", DOC_PREFIX,
        "SCHEMA",
        "text", "TEXT",
        "server", "TAG",
        "tool", "TAG",
        "doc_type", "TAG",
        "category", "TAG",
        "status", "TAG",
        "display_name", "TEXT",
        "chunk_index", "NUMERIC",
        "embedding", "VECTOR", "HNSW", "12",
        "TYPE", "FLOAT32",
        "DIM", str(dim),
        "DISTANCE_METRIC", DISTANCE_METRIC,
        "M", "16",
        "EF_CONSTRUCTION", "200",
        "EF_RUNTIME", "50",
    )
    logger.info("Created Redis vector index %s (dim=%d, prefix=%s)", INDEX_NAME, dim, DOC_PREFIX)
    return True


async def drop_index(delete_docs: bool = False) -> None:
    args = ["FT.DROPINDEX", INDEX_NAME]
    if delete_docs:
        args.append("DD")
    try:
        await get_client().execute_command(*args)
    except Exception as exc:  # noqa: BLE001
        logger.debug("drop_index: %s", exc)


async def upsert_doc(doc_id: str, mapping: Dict[str, object], embedding: List[float]) -> None:
    """Upsert a single document HASH with its embedding blob."""
    key = f"{DOC_PREFIX}{doc_id}"
    fields: Dict[str, object] = {}
    for k, v in mapping.items():
        if v is None:
            continue
        fields[k] = v if isinstance(v, (int, float, bytes, bytearray)) else str(v)
    fields["embedding"] = to_vector_bytes(embedding)
    await get_client().hset(key, mapping=fields)


async def delete_server_docs(server: str) -> int:
    """Delete every doc belonging to a server via key-prefix scan."""
    client = get_client()
    pattern = f"{DOC_PREFIX}{server}:*"
    deleted = 0
    cursor = 0
    while True:
        cursor, keys = await client.scan(cursor=cursor, match=pattern, count=500)
        if keys:
            deleted += await client.delete(*keys)
        if cursor == 0:
            break
    return deleted


async def set_server_status(server: str, status: str) -> int:
    """Update the ``status`` tag on all docs for a server (running/stopped/...)."""
    client = get_client()
    pattern = f"{DOC_PREFIX}{server}:*"
    updated = 0
    cursor = 0
    while True:
        cursor, keys = await client.scan(cursor=cursor, match=pattern, count=500)
        for key in keys:
            await client.hset(key, "status", status)
            updated += 1
        if cursor == 0:
            break
    return updated


async def search_knn(
    embedding: List[float],
    top_k: int = 20,
    doc_types: Optional[List[str]] = None,
    servers: Optional[List[str]] = None,
    statuses: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
) -> List[Dict[str, object]]:
    """Run a KNN vector search with optional TAG filters. Returns ranked docs."""
    filters = []
    if doc_types:
        filters.append(f"@doc_type:{{{'|'.join(escape_tag(t) for t in doc_types)}}}")
    if statuses:
        filters.append(f"@status:{{{'|'.join(escape_tag(s) for s in statuses)}}}")
    if servers:
        filters.append(f"@server:{{{'|'.join(escape_tag(s) for s in servers)}}}")
    if categories:
        filters.append(f"@category:{{{'|'.join(escape_tag(c) for c in categories)}}}")

    prefilter = " ".join(filters) if filters else "*"
    query = f"({prefilter})=>[KNN {top_k} @embedding $vec AS score]"

    raw = await get_client().execute_command(
        "FT.SEARCH", INDEX_NAME, query,
        "PARAMS", "2", "vec", to_vector_bytes(embedding),
        "RETURN", "6", "server", "tool", "doc_type", "category", "text", "score",
        "SORTBY", "score",
        "LIMIT", "0", str(top_k),
        "DIALECT", "2",
    )

    return _parse_search(raw)


def _score_fields(fields: Dict[str, object]) -> None:
    if "score" in fields:
        try:
            dist = float(fields["score"])
            fields["distance"] = dist
            fields["similarity"] = 1.0 - dist  # cosine distance -> similarity
        except (TypeError, ValueError):
            pass


def _parse_search(raw) -> List[Dict[str, object]]:
    """Parse an FT.SEARCH reply in either RESP2 (array) or RESP3 (map) form.

    RESP3 (redis-py >= 5 on a RESP3 connection / Redis Stack) returns a dict::

        {b'total_results': N, b'results': [{b'id': .., b'extra_attributes': {..}}]}

    RESP2 returns a flat array ``[total, key, [f, v, ...], key, [..]]``.
    """
    if isinstance(raw, dict):
        results: List[Dict[str, object]] = []
        rows = raw.get(b"results") or raw.get("results") or []
        for item in rows:
            if not isinstance(item, dict):
                continue
            item = {_decode(k): v for k, v in item.items()}
            fields: Dict[str, object] = {"_key": _decode(item.get("id"))}
            attrs = item.get("extra_attributes") or {}
            if isinstance(attrs, dict):
                for k, v in attrs.items():
                    fields[_decode(k)] = _decode(v)
            _score_fields(fields)
            results.append(fields)
        return results

    if not raw or not isinstance(raw, (list, tuple)):
        return []
    results = []
    # raw[0] = total; then repeating [key, [f, v, f, v, ...]]
    i = 1
    while i < len(raw):
        key = _decode(raw[i])
        fields_arr = raw[i + 1] if i + 1 < len(raw) else []
        i += 2
        fields = {"_key": key}
        if isinstance(fields_arr, (list, tuple)):
            for j in range(0, len(fields_arr) - 1, 2):
                fields[_decode(fields_arr[j])] = _decode(fields_arr[j + 1])
        _score_fields(fields)
        results.append(fields)
    return results


async def stats() -> Dict[str, object]:
    client = get_client()
    exists = await index_exists()
    doc_count = 0
    cursor = 0
    while True:
        cursor, keys = await client.scan(cursor=cursor, match=f"{DOC_PREFIX}*", count=1000)
        doc_count += len(keys)
        if cursor == 0:
            break
    info: Dict[str, object] = {
        "index": INDEX_NAME,
        "prefix": DOC_PREFIX,
        "exists": exists,
        "doc_count": doc_count,
        "dim": VECTOR_DIM,
        "redis_url": REDIS_URL,
    }
    return info


async def ping() -> bool:
    try:
        return bool(await get_client().ping())
    except Exception:
        return False
