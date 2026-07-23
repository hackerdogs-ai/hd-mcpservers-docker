"""
Indexing pipeline: turn MCP server metadata, READMEs, and tool lists into
embedded documents in the Redis vector index.

Document types (see docs/chat-assistant-ui.md §4.3):
  * server  — name + display name + category + short description
  * readme  — README chunks (split on ## headings)
  * tool    — tool name + description + input-schema summary
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Callable, Dict, List, Optional, Tuple

import embeddings
import vector_index

logger = logging.getLogger(__name__)

# Human-readable category labels (mirrors mcpfarm-ui/src/lib/categories.js).
CATEGORY_LABELS = {
    "core": "Core",
    "ai-security": "AI Security",
    "network-recon": "Network Recon",
    "web-app": "Web App",
    "appsec": "AppSec",
    "osint": "OSINT",
    "vuln-scanning": "Vuln Scanning",
    "binary-re": "Binary RE",
    "cloud-container": "Cloud",
    "exploitation": "Exploitation",
    "network-attacks": "Net Attacks",
    "threat-intel": "Threat Intel",
    "finance": "Finance",
    "geospatial": "Geospatial",
    "science": "Science & Health",
    "web-search": "Web & Search",
    "productivity": "Productivity",
    "devtools": "Dev Tools",
    "observability": "Observability",
    "data-ai": "Data & AI",
    "misc": "Misc",
}

MAX_README_CHUNKS = 20
CHUNK_TARGET_CHARS = 1800  # ~450-600 tokens
EMBED_BATCH = 64


def display_name(server: str) -> str:
    return re.sub(r"-mcp$", "", server or "")


def category_label(category: Optional[str]) -> str:
    return CATEGORY_LABELS.get(category or "", (category or "").replace("-", " ").title() or "Misc")


def chunk_readme(text: str) -> List[str]:
    """Split a README into chunks on ## headings, targeting ~CHUNK_TARGET_CHARS."""
    if not text:
        return []
    # Split keeping section headings.
    parts = re.split(r"\n(?=##\s)", text)
    chunks: List[str] = []
    buf = ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(buf) + len(part) + 1 <= CHUNK_TARGET_CHARS:
            buf = f"{buf}\n{part}".strip()
        else:
            if buf:
                chunks.append(buf)
            # A single oversized section is hard-split.
            if len(part) > CHUNK_TARGET_CHARS:
                for i in range(0, len(part), CHUNK_TARGET_CHARS):
                    chunks.append(part[i:i + CHUNK_TARGET_CHARS])
                buf = ""
            else:
                buf = part
    if buf:
        chunks.append(buf)
    return chunks[:MAX_README_CHUNKS]


def tool_schema_summary(tool: Dict) -> str:
    """Flatten an MCP tool input schema into a compact 'param: type' summary."""
    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    props = (schema or {}).get("properties") or {}
    parts = []
    for name, spec in props.items():
        typ = (spec or {}).get("type", "any")
        parts.append(f"{name}: {typ}")
    return ", ".join(parts)


def build_server_docs(
    server: str,
    category: Optional[str],
    status: str,
    readme_text: Optional[str],
    tools: Optional[List[Dict]],
) -> List[Tuple[str, Dict[str, object], str]]:
    """Return a list of (doc_id, mapping, text_to_embed)."""
    dn = display_name(server)
    clabel = category_label(category)
    docs: List[Tuple[str, Dict[str, object], str]] = []

    base_meta = {
        "server": server,
        "category": category or "",
        "status": status,
        "display_name": dn,
    }

    # server meta doc
    meta_text = f"{dn} {server} {clabel}. {dn} MCP server."
    docs.append((
        f"{server}:meta",
        {**base_meta, "doc_type": "server", "tool": "", "text": meta_text, "chunk_index": 0},
        meta_text,
    ))

    # readme chunks
    for idx, chunk in enumerate(chunk_readme(readme_text or "")):
        prefixed = f"Server: {dn} ({server}). Category: {clabel}.\n{chunk}"
        docs.append((
            f"{server}:readme:{idx}",
            {**base_meta, "doc_type": "readme", "tool": "", "text": chunk[:2000], "chunk_index": idx},
            prefixed,
        ))

    # tool docs
    for tool in (tools or []):
        tname = tool.get("name")
        if not tname:
            continue
        desc = tool.get("description") or ""
        summary = tool_schema_summary(tool)
        tool_text = f"{tname} {desc} {summary} ({dn})".strip()
        docs.append((
            f"{server}:tool:{tname}",
            {
                **base_meta,
                "doc_type": "tool",
                "tool": tname,
                "text": (desc or tname)[:1000],
                "chunk_index": 0,
            },
            tool_text,
        ))

    return docs


async def _embed_and_upsert(docs: List[Tuple[str, Dict[str, object], str]]) -> int:
    count = 0
    for start in range(0, len(docs), EMBED_BATCH):
        batch = docs[start:start + EMBED_BATCH]
        vecs = await embeddings.embed_texts([d[2] for d in batch])
        for (doc_id, mapping, _text), vec in zip(batch, vecs):
            await vector_index.upsert_doc(doc_id, mapping, vec)
            count += 1
    return count


async def index_server(
    server: str,
    category: Optional[str],
    status: str,
    readme_text: Optional[str],
    tools: Optional[List[Dict]] = None,
    replace: bool = True,
) -> int:
    """(Re)index a single server. Returns number of docs written."""
    await vector_index.ensure_index()
    if replace:
        await vector_index.delete_server_docs(server)
    docs = build_server_docs(server, category, status, readme_text, tools)
    return await _embed_and_upsert(docs)


async def reindex_all(
    servers: List[Dict],
    readme_loader: Callable[[str], Optional[str]],
    tools_loader: Optional[Callable[[Dict], "asyncio.Future"]] = None,
) -> Dict[str, object]:
    """Full reindex.

    ``servers``      — list of dicts with at least name/category/status.
    ``readme_loader``— sync fn(server_name) -> markdown text or None.
    ``tools_loader`` — optional async fn(server_dict) -> list[tool dict].
    """
    await vector_index.ensure_index()
    total_docs = 0
    indexed_servers = 0
    tool_servers = 0
    errors: List[str] = []

    for srv in servers:
        name = srv.get("name")
        if not name:
            continue
        status = _status_of(srv)
        try:
            readme_text = readme_loader(name)
        except Exception as exc:  # noqa: BLE001
            readme_text = None
            errors.append(f"{name} readme: {exc}")

        tools = None
        if tools_loader is not None and status == "running":
            try:
                tools = await tools_loader(srv)
                if tools:
                    tool_servers += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{name} tools: {exc}")

        try:
            n = await index_server(name, srv.get("category"), status, readme_text, tools)
            total_docs += n
            indexed_servers += 1
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{name} index: {exc}")

    return {
        "servers": indexed_servers,
        "tool_servers": tool_servers,
        "docs": total_docs,
        "errors": errors[:50],
        "error_count": len(errors),
    }


def _status_of(srv: Dict) -> str:
    """Health is authoritative: a server is only 'running' when it is healthy.

    The DB ``status`` column is set optimistically on start and can be stale, so
    we do not treat it as 'running' on its own — only ``health_ok`` does.
    """
    status = (srv.get("status") or "").lower()
    if status == "disabled":
        return "disabled"
    if srv.get("health_ok"):
        return "running"
    return "stopped"


# ---------------------------------------------------------------------------
# Internal MCP client (used to list tools during indexing, over the internal
# Docker network — no auth required between farm containers).
# ---------------------------------------------------------------------------

async def list_tools_internal(name: str, port: int, timeout: float = 8.0) -> List[Dict]:
    import httpx

    url = f"http://{name}:{port}/mcp"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        init = {
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "vector-indexer", "version": "1.0.0"},
            },
        }
        r = await client.post(url, json=init, headers=headers)
        r.raise_for_status()
        session = r.headers.get("mcp-session-id")
        h2 = dict(headers)
        if session:
            h2["mcp-session-id"] = session
        await client.post(url, json={"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}, headers=h2)
        r2 = await client.post(
            url,
            json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            headers=h2,
        )
        r2.raise_for_status()
        return _parse_tools_response(r2.text)


def _parse_tools_response(text: str) -> List[Dict]:
    payload = None
    for line in text.split("\n"):
        if line.startswith("data: "):
            try:
                payload = json.loads(line[6:])
                break
            except json.JSONDecodeError:
                continue
    if payload is None:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            return []
    if isinstance(payload, dict):
        result = payload.get("result") or {}
        return result.get("tools") or payload.get("tools") or []
    return []
