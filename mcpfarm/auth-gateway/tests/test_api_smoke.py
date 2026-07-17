"""
HTTP-level smoke tests for the new Chat endpoints, booting the real FastAPI
app with a temp SQLite DB and the shared hd-redis (isolated test namespace).

Run:  ./.venv-test/bin/python -m pytest tests/test_api_smoke.py -v
"""
import asyncio
import hashlib
import os
import sqlite3
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_NS = f"mcpfarmtest:{uuid.uuid4().hex[:8]}"
_DB = os.path.join(os.path.dirname(__file__), f"_smoke_{uuid.uuid4().hex[:6]}.db")
os.environ["AUTH_DB_PATH"] = _DB
os.environ["ADMIN_SECRET"] = "test-admin-secret"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["MCPFARM_VECTOR_PREFIX"] = _NS
os.environ["MCPFARM_VECTOR_INDEX"] = f"{_NS}:idx"
os.environ["EMBED_PROVIDER"] = "local"
os.environ["VECTOR_DIM"] = "256"
os.environ["MCPFARM_SECRETS_KEY"] = "Zt2m8n0p3q5r7s9u1w3y5A7C9E1G3I5K7M9O1Q3S5U7="

API_KEY = "hd_sk_" + "a" * 40
API_HASH = hashlib.sha256(API_KEY.encode()).hexdigest()


def _seed_db():
    con = sqlite3.connect(_DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY, key_hash TEXT, key_prefix TEXT, name TEXT,
            owner TEXT, scopes TEXT, rate_limit INTEGER, is_active INTEGER,
            created_at TEXT, expires_at TEXT, last_used TEXT)"""
    )
    con.execute(
        "INSERT INTO api_keys (id, key_hash, key_prefix, name, owner, scopes, rate_limit, is_active, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        ("t1", API_HASH, API_KEY[:12], "test", "test", "*", 100000, 1, "2024-01-01T00:00:00"),
    )
    con.commit()
    con.close()


def _reassert_env():
    """Another test module may have overwritten these at import; re-assert ours."""
    os.environ["AUTH_DB_PATH"] = _DB
    os.environ["ADMIN_SECRET"] = "test-admin-secret"
    os.environ["REDIS_URL"] = "redis://localhost:6379"
    os.environ["MCPFARM_VECTOR_PREFIX"] = _NS
    os.environ["MCPFARM_VECTOR_INDEX"] = f"{_NS}:idx"
    os.environ["EMBED_PROVIDER"] = "local"
    os.environ["VECTOR_DIM"] = "256"
    os.environ["MCPFARM_SECRETS_KEY"] = "Zt2m8n0p3q5r7s9u1w3y5A7C9E1G3I5K7M9O1Q3S5U7="


@pytest.fixture(scope="module")
def client():
    _reassert_env()
    _seed_db()

    # Reload config-capturing modules so they bind to THIS module's env
    # regardless of test collection order.
    import importlib
    import embeddings
    import vector_index
    import vector_indexer
    import secrets_vault
    import chat_proxy
    for mod in (embeddings, vector_index, vector_indexer, secrets_vault, chat_proxy):
        importlib.reload(mod)
    from fastapi.testclient import TestClient
    import main
    importlib.reload(main)

    # Seed the vector index with a couple of servers so /vectors/search works.
    async def _seed_vectors():
        if not await vector_index.ping():
            return False
        await vector_index.drop_index(delete_docs=True)
        await vector_indexer.index_server(
            "nmap-mcp", "network-recon", "running",
            "# Nmap\n## Tools\nNmap scans hosts for open TCP/UDP ports and detects running services.",
            [{"name": "run_nmap", "description": "Run an nmap port and service scan",
              "inputSchema": {"properties": {"arguments": {"type": "string"}}}}],
        )
        await vector_indexer.index_server(
            "sqlmap-mcp", "web-app", "running",
            "# sqlmap\n## Tools\nsqlmap automates SQL injection discovery and exploitation.",
            [{"name": "run_sqlmap", "description": "Test a URL for SQL injection",
              "inputSchema": {"properties": {"url": {"type": "string"}}}}],
        )
        return True

    has_redis = asyncio.get_event_loop().run_until_complete(_seed_vectors())

    with TestClient(main.app) as c:
        c._has_redis = has_redis
        yield c

    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(_DB + suffix)
        except OSError:
            pass
    # Best-effort redis cleanup on a fresh loop + fresh client (the cached
    # client was bound to the now-closed TestClient loop).
    async def _cleanup():
        vector_index._client = None
        try:
            await vector_index.delete_server_docs("nmap-mcp")
            await vector_index.delete_server_docs("sqlmap-mcp")
            await vector_index.drop_index(delete_docs=True)
        finally:
            client = vector_index.get_client()
            await client.aclose()
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_cleanup())
    except Exception:
        pass
    finally:
        loop.close()


ADMIN = {"X-Admin-Secret": "test-admin-secret", "Authorization": f"Bearer {API_KEY}"}
USER = {"Authorization": f"Bearer {API_KEY}"}


def test_health(client):
    assert client.get("/health").status_code == 200


def test_llm_keys_lifecycle(client):
    r = client.get("/llm-keys", headers=ADMIN)
    assert r.status_code == 200
    assert "claude" in r.json()["providers"]

    r = client.put("/llm-keys/openai", json={"key": "sk-smoke-abcdefgh12345678"}, headers=ADMIN)
    assert r.status_code == 200
    body = r.json()
    assert body["has_key"] is True
    assert "abcdefgh" not in body["key_prefix"]  # masked

    r = client.get("/llm-keys", headers=ADMIN)
    providers = {k["provider"] for k in r.json()["keys"]}
    assert "openai" in providers

    r = client.delete("/llm-keys/openai", headers=ADMIN)
    assert r.status_code == 200


def test_llm_keys_require_admin(client):
    assert client.get("/llm-keys", headers=USER).status_code == 403


def test_chat_requires_key(client):
    # No claude key configured -> 400 with a helpful message (no network call).
    r = client.post("/chat/completions", headers=USER,
                    json={"provider": "claude", "messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 400
    assert "key" in r.json()["detail"].lower()


def test_chat_unknown_provider(client):
    r = client.post("/chat/completions", headers=USER,
                    json={"provider": "nope", "messages": []})
    assert r.status_code == 400


def test_chat_requires_auth(client):
    r = client.post("/chat/completions", json={"provider": "claude", "messages": []})
    assert r.status_code == 401


def test_vector_search(client):
    if not getattr(client, "_has_redis", False):
        pytest.skip("hd-redis not reachable")
    r = client.post("/vectors/search", headers=USER,
                    json={"query": "scan a host for open network ports", "top_k_servers": 3})
    assert r.status_code == 200
    data = r.json()
    assert "nmap-mcp" in data["servers"]
    assert any(t["tool"] == "run_nmap" for t in data["tools"])


def test_vector_stats(client):
    if not getattr(client, "_has_redis", False):
        pytest.skip("hd-redis not reachable")
    r = client.get("/admin/vectors/stats", headers=ADMIN)
    assert r.status_code == 200
    assert r.json()["index"].startswith(_NS)
