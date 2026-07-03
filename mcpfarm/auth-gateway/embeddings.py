"""
Embedding providers for the MCP Farm vector index.

Supports three backends, selected via ``EMBED_PROVIDER`` (or auto-detected):

* ``openai`` — ``text-embedding-3-small`` (1536 dims) via the OpenAI API.
* ``ollama`` — a local embedding model (e.g. ``nomic-embed-text``).
* ``local``  — a dependency-free deterministic hashing embedder. Produces
  keyword-overlap-sensitive vectors so semantic-ish search works offline and
  in tests without any API keys.

All providers return vectors of exactly ``VECTOR_DIM`` dimensions so a single
Redis index schema stays valid regardless of the active provider.
"""
from __future__ import annotations

import hashlib
import logging
import math
import os
import re
from typing import List

import httpx

logger = logging.getLogger(__name__)

VECTOR_DIM = int(os.environ.get("VECTOR_DIM", "1536"))

_EMBED_PROVIDER = os.environ.get("EMBED_PROVIDER", "auto").lower()
_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
_OPENAI_EMBED_MODEL = os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
_OPENAI_BASE = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
_OLLAMA_URL = os.environ.get("OLLAMA_URL", "").rstrip("/")
_OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def resolve_provider() -> str:
    """Return the active embedding provider id."""
    if _EMBED_PROVIDER in ("openai", "ollama", "local"):
        return _EMBED_PROVIDER
    if _OPENAI_API_KEY:
        return "openai"
    if _OLLAMA_URL:
        return "ollama"
    return "local"


def _fit_dim(vec: List[float]) -> List[float]:
    """Pad or truncate a vector to exactly ``VECTOR_DIM`` dimensions."""
    n = len(vec)
    if n == VECTOR_DIM:
        return vec
    if n > VECTOR_DIM:
        return vec[:VECTOR_DIM]
    return vec + [0.0] * (VECTOR_DIM - n)


def _l2_normalize(vec: List[float]) -> List[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]


def _local_embed_one(text: str) -> List[float]:
    """Deterministic feature-hashing embedding (the "hashing trick").

    Each token is hashed into a bucket with a signed contribution. Cosine
    similarity between two such vectors tracks their shared-token overlap, which
    is good enough for offline / test-time semantic-ish retrieval.
    """
    vec = [0.0] * VECTOR_DIM
    tokens = _TOKEN_RE.findall((text or "").lower())
    for tok in tokens:
        h = hashlib.md5(tok.encode("utf-8")).digest()
        bucket = int.from_bytes(h[:4], "little") % VECTOR_DIM
        sign = 1.0 if (h[4] & 1) else -1.0
        vec[bucket] += sign
    return _l2_normalize(vec)


def _local_embed(texts: List[str]) -> List[List[float]]:
    return [_local_embed_one(t) for t in texts]


async def _openai_embed(texts: List[str]) -> List[List[float]]:
    if not _OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set for openai embeddings")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{_OPENAI_BASE}/embeddings",
            headers={"Authorization": f"Bearer {_OPENAI_API_KEY}"},
            json={"model": _OPENAI_EMBED_MODEL, "input": texts},
        )
    resp.raise_for_status()
    data = resp.json()
    ordered = sorted(data["data"], key=lambda d: d["index"])
    return [_fit_dim([float(x) for x in d["embedding"]]) for d in ordered]


async def _ollama_embed(texts: List[str]) -> List[List[float]]:
    if not _OLLAMA_URL:
        raise RuntimeError("OLLAMA_URL not set for ollama embeddings")
    out: List[List[float]] = []
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Prefer the batch /api/embed endpoint; fall back to per-text /api/embeddings.
        try:
            resp = await client.post(
                f"{_OLLAMA_URL}/api/embed",
                json={"model": _OLLAMA_EMBED_MODEL, "input": texts},
            )
            resp.raise_for_status()
            data = resp.json()
            embs = data.get("embeddings")
            if embs:
                return [_fit_dim([float(x) for x in e]) for e in embs]
        except Exception as exc:  # noqa: BLE001 — fall back below
            logger.debug("ollama /api/embed failed, falling back: %s", exc)
        for text in texts:
            resp = await client.post(
                f"{_OLLAMA_URL}/api/embeddings",
                json={"model": _OLLAMA_EMBED_MODEL, "prompt": text},
            )
            resp.raise_for_status()
            emb = resp.json().get("embedding", [])
            out.append(_fit_dim([float(x) for x in emb]))
    return out


async def embed_texts(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts with the active provider.

    Falls back to the local embedder if the remote provider errors so indexing
    never hard-fails on a transient API problem.
    """
    if not texts:
        return []
    provider = resolve_provider()
    try:
        if provider == "openai":
            return await _openai_embed(texts)
        if provider == "ollama":
            return await _ollama_embed(texts)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding provider '%s' failed (%s); using local fallback", provider, exc)
    return _local_embed(texts)


async def embed_text(text: str) -> List[float]:
    return (await embed_texts([text]))[0]
