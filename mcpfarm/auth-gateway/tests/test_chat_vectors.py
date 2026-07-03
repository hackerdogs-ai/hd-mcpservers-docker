"""
Tests for the Chat / vector-search backend.

Redis tests target the shared hd-redis on localhost:6379 (exposed by the
container) and use a throwaway index name + key prefix so they never touch
other services' data. Run:

    ./.venv-test/bin/python -m pytest tests/ -v
"""
import os
import sys
import uuid

import pytest

# Import modules under test (auth-gateway dir is the parent of tests/).
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Point everything at an isolated test namespace BEFORE importing modules.
_TEST_NS = f"mcpfarmtest:{uuid.uuid4().hex[:8]}"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ["MCPFARM_VECTOR_PREFIX"] = _TEST_NS
os.environ["MCPFARM_VECTOR_INDEX"] = f"{_TEST_NS}:idx"
os.environ["EMBED_PROVIDER"] = "local"
os.environ["VECTOR_DIM"] = "256"
os.environ["AUTH_DB_PATH"] = os.path.join(os.path.dirname(__file__), f"_test_auth_{uuid.uuid4().hex[:6]}.db")
os.environ["MCPFARM_SECRETS_KEY"] = "Zt2m8n0p3q5r7s9u1w3y5A7C9E1G3I5K7M9O1Q3S5U7="  # test-only 32B base64

import chat_proxy  # noqa: E402
import embeddings  # noqa: E402
import secrets_vault  # noqa: E402
import vector_index  # noqa: E402
import vector_indexer  # noqa: E402


# --------------------------------------------------------------------------- embeddings

def test_local_embedding_dim_and_determinism():
    a = embeddings._local_embed_one("scan open ports on a host")
    b = embeddings._local_embed_one("scan open ports on a host")
    assert len(a) == 256
    assert a == b  # deterministic


def test_local_embedding_similarity_ordering():
    import math

    def cos(x, y):
        return sum(i * j for i, j in zip(x, y))  # already L2-normalized

    q = embeddings._local_embed_one("scan ports network nmap")
    near = embeddings._local_embed_one("nmap network port scanner")
    far = embeddings._local_embed_one("generate a financial spreadsheet report")
    assert cos(q, near) > cos(q, far)


# --------------------------------------------------------------------------- indexer helpers

def test_chunk_readme_splits_on_headings():
    text = "# Title\nintro\n\n## Tools\n" + ("a " * 20) + "\n\n## Usage\n" + ("b " * 20)
    chunks = vector_indexer.chunk_readme(text)
    assert len(chunks) >= 1
    assert any("Tools" in c or "Usage" in c for c in chunks)


def test_tool_schema_summary():
    tool = {"name": "run_nmap", "inputSchema": {"type": "object", "properties": {
        "arguments": {"type": "string"}, "timeout_seconds": {"type": "integer"}}}}
    summary = vector_indexer.tool_schema_summary(tool)
    assert "arguments: string" in summary
    assert "timeout_seconds: integer" in summary


def test_build_server_docs_shapes():
    docs = vector_indexer.build_server_docs(
        "nmap-mcp", "network-recon", "running",
        "# Nmap\n## Tools\nport scanning tool",
        [{"name": "run_nmap", "description": "Run nmap", "inputSchema": {"properties": {"arguments": {"type": "string"}}}}],
    )
    kinds = {d[1]["doc_type"] for d in docs}
    assert {"server", "readme", "tool"} <= kinds
    tool_doc = next(d for d in docs if d[1]["doc_type"] == "tool")
    assert tool_doc[1]["tool"] == "run_nmap"
    assert tool_doc[1]["server"] == "nmap-mcp"


# --------------------------------------------------------------------------- secrets vault

@pytest.mark.asyncio
async def test_secrets_vault_roundtrip():
    await secrets_vault.init_db()
    await secrets_vault.set_secret("openai", "sk-test-1234567890abcdef")
    assert await secrets_vault.get_secret("openai") == "sk-test-1234567890abcdef"
    listed = await secrets_vault.list_secrets()
    entry = next(e for e in listed if e["provider"] == "openai")
    assert entry["has_key"] is True
    assert "1234567890abcdef" not in entry["key_prefix"]  # masked
    await secrets_vault.delete_secret("openai")
    assert await secrets_vault.get_secret("openai") is None


@pytest.mark.asyncio
async def test_secrets_vault_wrong_key_fails_gracefully():
    await secrets_vault.init_db()
    await secrets_vault.set_secret("grok", "xai-secret-value")
    # Corrupt the cached fernet with a different key.
    from cryptography.fernet import Fernet
    original = secrets_vault._fernet
    secrets_vault._fernet = Fernet(Fernet.generate_key())
    try:
        assert await secrets_vault.get_secret("grok") is None  # cannot decrypt
    finally:
        secrets_vault._fernet = original
    await secrets_vault.delete_secret("grok")


# --------------------------------------------------------------------------- chat_proxy conversions

def test_messages_to_openai_tool_roundtrip():
    msgs = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "", "toolCalls": [{"id": "c1", "name": "run_nmap", "arguments": {"arguments": "-sV x"}}]},
        {"role": "tool", "tool_call_id": "c1", "content": "open: 80"},
    ]
    out = chat_proxy._messages_to_openai(msgs)
    assert out[1]["tool_calls"][0]["function"]["name"] == "run_nmap"
    assert out[2]["role"] == "tool" and out[2]["tool_call_id"] == "c1"


def test_messages_to_claude_system_extraction():
    msgs = [
        {"role": "system", "content": "be terse"},
        {"role": "user", "content": "scan"},
        {"role": "assistant", "content": "ok", "toolCalls": [{"id": "c1", "name": "t", "arguments": {}}]},
        {"role": "tool", "tool_use_id": "c1", "content": "res"},
    ]
    cmsgs, system = chat_proxy._messages_to_claude(msgs)
    assert system == "be terse"
    assert cmsgs[1]["content"][1]["type"] == "tool_use"
    assert cmsgs[2]["content"][0]["type"] == "tool_result"


def test_parse_openai_response_tool_calls():
    data = {"choices": [{"message": {"content": "", "tool_calls": [
        {"id": "c1", "function": {"name": "run_nmap", "arguments": '{"arguments":"-sV"}'}}]}}]}
    parsed = chat_proxy._parse_openai_response(data, "OpenAI")
    assert parsed["toolCalls"][0]["name"] == "run_nmap"
    assert parsed["toolCalls"][0]["arguments"] == {"arguments": "-sV"}


def test_parse_claude_response_text():
    data = {"content": [{"type": "text", "text": "hello"}]}
    parsed = chat_proxy._parse_claude_response(data)
    assert parsed["content"] == "hello"
    assert parsed["toolCalls"] == []


def test_messages_to_ollama_keeps_arguments_as_object():
    # Ollama's /api/chat rejects stringified tool-call arguments and null content.
    msgs = [
        {"role": "assistant", "content": "", "toolCalls": [
            {"id": "c1", "name": "whois_lookup", "arguments": {"domain": "example.com"}}]},
        {"role": "tool", "tool_call_id": "c1", "name": "whois_lookup", "content": "{...}"},
    ]
    out = chat_proxy._messages_to_ollama(msgs)
    tc = out[0]["tool_calls"][0]
    assert tc["function"]["name"] == "whois_lookup"
    assert tc["function"]["arguments"] == {"domain": "example.com"}  # object, not JSON string
    assert out[0]["content"] == ""  # never null
    assert out[1]["role"] == "tool" and out[1]["tool_name"] == "whois_lookup"


# --------------------------------------------------------------------------- FT.SEARCH reply parsing

def test_parse_search_handles_resp2_array():
    # RESP2 (redis-py < 8 default): flat [total, key, [f, v, ...]]
    raw = [1, b"mcpfarm:v1:doc:nmap-mcp:meta",
           [b"server", b"nmap-mcp", b"doc_type", b"server", b"score", b"0.2"]]
    rows = vector_index._parse_search(raw)
    assert len(rows) == 1
    assert rows[0]["server"] == "nmap-mcp"
    assert abs(rows[0]["similarity"] - 0.8) < 1e-9


def test_parse_search_handles_resp3_map():
    # RESP3 (redis-py >= 8 on Redis Stack): {total_results, results:[{id, extra_attributes}]}
    raw = {
        b"total_results": 1,
        b"results": [
            {b"id": b"mcpfarm:v1:doc:nmap-mcp:meta",
             b"extra_attributes": {b"server": b"nmap-mcp", b"doc_type": b"server", b"score": b"0.25"}},
        ],
    }
    rows = vector_index._parse_search(raw)
    assert len(rows) == 1
    assert rows[0]["server"] == "nmap-mcp"
    assert rows[0]["doc_type"] == "server"
    assert abs(rows[0]["similarity"] - 0.75) < 1e-9


# --------------------------------------------------------------------------- status resolution

def test_status_of_is_health_authoritative():
    # DB status='running' but unhealthy -> stopped (stale optimistic status ignored)
    assert vector_indexer._status_of({"status": "running", "health_ok": 0}) == "stopped"
    assert vector_indexer._status_of({"status": "running", "health_ok": 1}) == "running"
    assert vector_indexer._status_of({"status": "stopped", "health_ok": 1}) == "running"
    assert vector_indexer._status_of({"status": "disabled", "health_ok": 1}) == "disabled"


# --------------------------------------------------------------------------- live Redis vector index

@pytest.mark.asyncio
async def test_redis_index_and_search():
    if not await vector_index.ping():
        pytest.skip("hd-redis not reachable on localhost:6379")

    await vector_index.drop_index(delete_docs=True)
    created = await vector_index.ensure_index()
    assert created is True

    servers = [
        {"name": "nmap-mcp", "category": "network-recon", "status": "running", "health_ok": True,
         "readme": "# Nmap\n## Tools\nNmap scans hosts for open ports and running services.",
         "tools": [{"name": "run_nmap", "description": "Run an nmap port and service scan",
                    "inputSchema": {"properties": {"arguments": {"type": "string"}}}}]},
        {"name": "sqlmap-mcp", "category": "web-app", "status": "running", "health_ok": True,
         "readme": "# sqlmap\n## Tools\nsqlmap automates SQL injection detection and exploitation.",
         "tools": [{"name": "run_sqlmap", "description": "Test a URL for SQL injection",
                    "inputSchema": {"properties": {"url": {"type": "string"}}}}]},
        {"name": "trivy-mcp", "category": "cloud-container", "status": "stopped", "health_ok": False,
         "readme": "# Trivy\n## Tools\nTrivy scans container images for vulnerabilities.",
         "tools": []},
    ]

    for s in servers:
        await vector_indexer.index_server(
            s["name"], s["category"], vector_indexer._status_of(s), s["readme"], s.get("tools"))

    # Stage-1 style: discover servers for a port-scanning query.
    qvec = await embeddings.embed_text("scan a host for open network ports")
    hits = await vector_index.search_knn(qvec, top_k=10, doc_types=["server", "readme"], statuses=["running"])
    servers_found = [h.get("server") for h in hits]
    assert "nmap-mcp" in servers_found
    # stopped server must be filtered out by status tag
    assert "trivy-mcp" not in servers_found

    # Stage-2: tool ranking within nmap-mcp.
    tool_hits = await vector_index.search_knn(
        qvec, top_k=5, doc_types=["tool"], servers=["nmap-mcp"], statuses=["running"])
    assert any(h.get("tool") == "run_nmap" for h in tool_hits)

    # Status update flips a running server to stopped and removes it from results.
    await vector_index.set_server_status("nmap-mcp", "stopped")
    hits2 = await vector_index.search_knn(qvec, top_k=10, doc_types=["server", "readme"], statuses=["running"])
    assert "nmap-mcp" not in [h.get("server") for h in hits2]

    # Delete docs for a server.
    deleted = await vector_index.delete_server_docs("sqlmap-mcp")
    assert deleted > 0

    stats = await vector_index.stats()
    assert stats["exists"] is True

    # Cleanup: drop the throwaway index + docs.
    await vector_index.delete_server_docs("nmap-mcp")
    await vector_index.delete_server_docs("trivy-mcp")
    await vector_index.drop_index(delete_docs=True)
