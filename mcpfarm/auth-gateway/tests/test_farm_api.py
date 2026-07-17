"""
Comprehensive API integration tests for the MCP Farm auth-gateway.

Covers: health, server CRUD, search, batch operations, API key lifecycle,
LLM keys, export, stats, audit, and the new automation endpoints.

Run:  ./.venv-test/bin/python -m pytest tests/test_farm_api.py -v
"""
import hashlib
import os
import sqlite3
import sys
import uuid

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_DB = os.path.join(os.path.dirname(__file__), f"_farm_{uuid.uuid4().hex[:6]}.db")
_NS = f"mcpfarmtest:{uuid.uuid4().hex[:8]}"
os.environ["AUTH_DB_PATH"] = _DB
os.environ["ADMIN_SECRET"] = "test-admin-secret"
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["MCPFARM_VECTOR_PREFIX"] = _NS
os.environ["MCPFARM_VECTOR_INDEX"] = f"{_NS}:idx"
os.environ["EMBED_PROVIDER"] = "local"
os.environ["VECTOR_DIM"] = "256"
os.environ["MCPFARM_SECRETS_KEY"] = "Zt2m8n0p3q5r7s9u1w3y5A7C9E1G3I5K7M9O1Q3S5U7="
os.environ["READMES_ROOT"] = ""

API_KEY = "hd_sk_" + "b" * 40
API_HASH = hashlib.sha256(API_KEY.encode()).hexdigest()
BAD_KEY = "hd_sk_" + "x" * 40


def _seed_db():
    con = sqlite3.connect(_DB)
    con.execute(
        """CREATE TABLE IF NOT EXISTS api_keys (
            id TEXT PRIMARY KEY, key_hash TEXT, key_prefix TEXT, name TEXT,
            owner TEXT, scopes TEXT, rate_limit INTEGER, is_active INTEGER,
            created_at TEXT, expires_at TEXT, last_used TEXT)"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS servers (
            name TEXT PRIMARY KEY, image TEXT, port INTEGER, env TEXT,
            status TEXT DEFAULT 'stopped', source TEXT DEFAULT 'seed',
            category TEXT DEFAULT '', url TEXT DEFAULT NULL,
            created_at TEXT, last_health TEXT, health_ok INTEGER DEFAULT 0)"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, key_id TEXT NOT NULL,
            server TEXT NOT NULL, method TEXT NOT NULL, status INTEGER NOT NULL,
            latency_ms INTEGER NOT NULL, created_at TEXT NOT NULL)"""
    )
    con.execute(
        "INSERT OR REPLACE INTO api_keys (id, key_hash, key_prefix, name, owner, scopes, rate_limit, is_active, created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        ("farmtest", API_HASH, API_KEY[:12], "farm-test", "test", "*", 100000, 1, "2024-01-01T00:00:00"),
    )
    con.execute(
        "INSERT OR REPLACE INTO servers (name, image, port, env, status, source, category, created_at, health_ok) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        ("nmap-mcp", "hackerdogs/nmap-mcp:latest", 8101, "[]", "running", "seed", "recon", "2024-01-01", 1),
    )
    con.execute(
        "INSERT OR REPLACE INTO servers (name, image, port, env, status, source, category, created_at, health_ok) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        ("sqlmap-mcp", "hackerdogs/sqlmap-mcp:latest", 8102, "[]", "stopped", "seed", "web-app", "2024-01-01", 0),
    )
    con.execute(
        "INSERT OR REPLACE INTO servers (name, image, port, env, status, source, category, created_at, health_ok) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        ("trivy-mcp", "hackerdogs/trivy-mcp:latest", 8103, "[]", "running", "seed", "cloud", "2024-01-01", 1),
    )
    con.commit()
    con.close()


@pytest.fixture(scope="module")
def client():
    os.environ["AUTH_DB_PATH"] = _DB
    os.environ["ADMIN_SECRET"] = "test-admin-secret"
    _seed_db()

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

    with TestClient(main.app) as c:
        yield c

    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(_DB + suffix)
        except OSError:
            pass


ADMIN = {"X-Admin-Secret": "test-admin-secret", "Authorization": f"Bearer {API_KEY}"}
USER = {"Authorization": f"Bearer {API_KEY}"}


# ─── Health ─────────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200

    def test_ui_config(self, client):
        r = client.get("/ui-config")
        assert r.status_code == 200


# ─── Auth ───────────────────────────────────────────────────────────────────

class TestAuth:
    def test_admin_endpoint_requires_secret(self, client):
        r = client.get("/admin/servers", headers=USER)
        assert r.status_code == 403

    def test_admin_endpoint_with_secret(self, client):
        r = client.get("/admin/servers", headers=ADMIN)
        assert r.status_code == 200

    def test_bad_api_key_rejected(self, client):
        r = client.post("/chat/completions", headers={"Authorization": f"Bearer {BAD_KEY}"},
                        json={"provider": "claude", "messages": []})
        assert r.status_code == 401

    def test_no_auth_rejected(self, client):
        r = client.post("/chat/completions", json={"provider": "claude", "messages": []})
        assert r.status_code == 401


# ─── Server listing ─────────────────────────────────────────────────────────

class TestServerListing:
    def test_list_services_public(self, client):
        r = client.get("/services", headers=USER)
        assert r.status_code == 200
        names = [s["name"] for s in r.json()]
        assert "nmap-mcp" in names

    def test_list_servers_admin(self, client):
        r = client.get("/admin/servers", headers=ADMIN)
        assert r.status_code == 200
        assert len(r.json()) >= 3

    def test_get_single_server(self, client):
        r = client.get("/admin/servers/nmap-mcp", headers=ADMIN)
        assert r.status_code == 200
        assert r.json()["name"] == "nmap-mcp"

    def test_get_nonexistent_server(self, client):
        r = client.get("/admin/servers/does-not-exist-mcp", headers=ADMIN)
        assert r.status_code == 404


# ─── Server CRUD ────────────────────────────────────────────────────────────

class TestServerCRUD:
    def test_create_external_server(self, client):
        r = client.post("/admin/servers", headers=ADMIN, json={
            "name": "test-external-mcp",
            "url": "https://example.com/mcp",
            "category": "test",
        })
        assert r.status_code == 200
        assert r.json()["name"] == "test-external-mcp"
        assert r.json()["source"] == "external"

    def test_create_duplicate_fails(self, client):
        r = client.post("/admin/servers", headers=ADMIN, json={
            "name": "test-external-mcp",
            "url": "https://example.com/mcp",
        })
        assert r.status_code in (400, 409, 500)

    def test_delete_server(self, client):
        r = client.delete("/admin/servers/test-external-mcp", headers=ADMIN)
        assert r.status_code == 200
        assert r.json()["deleted"] == "test-external-mcp"

    def test_delete_nonexistent(self, client):
        r = client.delete("/admin/servers/does-not-exist-mcp", headers=ADMIN)
        assert r.status_code == 404


# ─── Server Search ──────────────────────────────────────────────────────────

class TestServerSearch:
    def test_search_by_name(self, client):
        r = client.get("/admin/servers/search?q=nmap", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert data["count"] >= 1
        assert any(s["name"] == "nmap-mcp" for s in data["servers"])

    def test_search_by_category(self, client):
        r = client.get("/admin/servers/search?category=recon", headers=ADMIN)
        assert r.status_code == 200
        for s in r.json()["servers"]:
            assert s["category"] == "recon"

    def test_search_by_status(self, client):
        r = client.get("/admin/servers/search?status=running", headers=ADMIN)
        assert r.status_code == 200
        for s in r.json()["servers"]:
            assert s["status"] == "running"

    def test_search_by_health(self, client):
        r = client.get("/admin/servers/search?healthy=true", headers=ADMIN)
        assert r.status_code == 200
        assert r.json()["count"] >= 1

    def test_search_no_results(self, client):
        r = client.get("/admin/servers/search?q=zzzznotexist", headers=ADMIN)
        assert r.status_code == 200
        assert r.json()["count"] == 0

    def test_search_combined_filters(self, client):
        r = client.get("/admin/servers/search?category=recon&status=running", headers=ADMIN)
        assert r.status_code == 200
        for s in r.json()["servers"]:
            assert s["category"] == "recon"
            assert s["status"] == "running"


# ─── Categories ─────────────────────────────────────────────────────────────

class TestCategories:
    def test_list_categories(self, client):
        r = client.get("/admin/servers/categories", headers=ADMIN)
        assert r.status_code == 200
        cats = r.json()["categories"]
        assert len(cats) >= 1
        cat_names = [c["category"] for c in cats]
        assert "recon" in cat_names


# ─── Batch Operations ───────────────────────────────────────────────────────

class TestBatchOps:
    def test_batch_invalid_action(self, client):
        r = client.post("/admin/servers/batch", headers=ADMIN, json={
            "servers": ["nmap-mcp"],
            "action": "explode",
        })
        assert r.status_code == 400

    def test_batch_stop(self, client):
        r = client.post("/admin/servers/batch", headers=ADMIN, json={
            "servers": ["nmap-mcp", "trivy-mcp"],
            "action": "stop",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["action"] == "stop"
        assert data["total"] == 2

    def test_batch_with_nonexistent(self, client):
        r = client.post("/admin/servers/batch", headers=ADMIN, json={
            "servers": ["nmap-mcp", "ghost-mcp"],
            "action": "stop",
        })
        assert r.status_code == 200
        results = r.json()["results"]
        ghost = next(r for r in results if r["name"] == "ghost-mcp")
        assert ghost["status"] == "error"

    def test_batch_health_check_all(self, client):
        r = client.post("/admin/servers/health-check", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "healthy" in data
        assert "unhealthy" in data
        assert data["total"] >= 3

    def test_batch_health_check_subset(self, client):
        r = client.post("/admin/servers/health-check", headers=ADMIN,
                        json=["nmap-mcp", "sqlmap-mcp"])
        assert r.status_code == 200
        assert r.json()["total"] == 2


# ─── API Key Lifecycle ──────────────────────────────────────────────────────

class TestAPIKeys:
    def test_list_keys(self, client):
        r = client.get("/admin/keys", headers=ADMIN)
        assert r.status_code == 200

    def test_create_and_delete_key(self, client):
        r = client.post("/admin/keys", headers=ADMIN, json={"name": "test-automation"})
        assert r.status_code == 200
        key_id = r.json()["id"]
        raw_key = r.json()["key"]
        assert raw_key.startswith("hd_sk_")

        r = client.get(f"/admin/keys/{key_id}", headers=ADMIN)
        assert r.status_code == 200

        r = client.delete(f"/admin/keys/{key_id}", headers=ADMIN)
        assert r.status_code == 200

    def test_update_key(self, client):
        r = client.post("/admin/keys", headers=ADMIN, json={"name": "update-test"})
        key_id = r.json()["id"]

        r = client.patch(f"/admin/keys/{key_id}", headers=ADMIN, json={"is_active": False})
        assert r.status_code == 200

        r = client.delete(f"/admin/keys/{key_id}", headers=ADMIN)
        assert r.status_code == 200


# ─── LLM Keys ──────────────────────────────────────────────────────────────

class TestLLMKeys:
    def test_llm_key_lifecycle(self, client):
        r = client.get("/llm-keys", headers=ADMIN)
        assert r.status_code == 200
        assert "providers" in r.json()

        r = client.put("/llm-keys/openai", headers=ADMIN, json={"key": "sk-test-automation-key"})
        assert r.status_code == 200

        r = client.get("/llm-keys", headers=ADMIN)
        providers = {k["provider"] for k in r.json()["keys"]}
        assert "openai" in providers

        r = client.delete("/llm-keys/openai", headers=ADMIN)
        assert r.status_code == 200

    def test_llm_keys_require_admin(self, client):
        r = client.get("/llm-keys", headers=USER)
        assert r.status_code == 403

    def test_llm_unknown_provider(self, client):
        r = client.put("/llm-keys/fakeprovider", headers=ADMIN, json={"key": "x"})
        assert r.status_code == 400


# ─── Stats & Audit ──────────────────────────────────────────────────────────

class TestStatsAudit:
    def test_farm_stats(self, client):
        r = client.get("/admin/stats", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert "total_servers" in data
        assert "total_keys" in data

    def test_audit_log(self, client):
        r = client.get("/admin/audit", headers=ADMIN)
        assert r.status_code == 200

    def test_audit_filter_by_server(self, client):
        r = client.get("/admin/audit?server=nmap-mcp", headers=ADMIN)
        assert r.status_code == 200


# ─── Export & Reload ────────────────────────────────────────────────────────

class TestExportReload:
    def test_export(self, client):
        r = client.get("/admin/export", headers=ADMIN)
        assert r.status_code == 200
        data = r.json()
        assert "servers" in data
        assert "keys" in data

    def test_reload_caddy(self, client):
        r = client.post("/admin/reload", headers=ADMIN)
        # May fail if Caddy isn't running, but should not 500
        assert r.status_code in (200, 502)


# ─── Import ─────────────────────────────────────────────────────────────────

class TestImport:
    def test_import_external_server(self, client):
        r = client.post("/admin/servers/import", headers=ADMIN, json={
            "mcpServers": {
                "import-test": {
                    "url": "https://import-test.example.com/mcp",
                }
            }
        })
        assert r.status_code == 200
        data = r.json()
        assert data["imported"] == 1

        client.delete("/admin/servers/import-test-mcp", headers=ADMIN)

    def test_import_duplicate_skipped(self, client):
        r = client.post("/admin/servers/import", headers=ADMIN, json={
            "mcpServers": {
                "nmap": {"url": "https://example.com/mcp"}
            }
        })
        assert r.status_code == 200
        result = r.json()["results"][0]
        assert result["status"] == "skipped"


# ─── Chat Completions ──────────────────────────────────────────────────────

class TestChat:
    def test_chat_requires_auth(self, client):
        r = client.post("/chat/completions", json={"provider": "claude", "messages": []})
        assert r.status_code == 401

    def test_chat_unknown_provider(self, client):
        r = client.post("/chat/completions", headers=USER,
                        json={"provider": "nope", "messages": []})
        assert r.status_code == 400

    def test_chat_no_key_configured(self, client):
        r = client.post("/chat/completions", headers=USER,
                        json={"provider": "claude", "messages": [{"role": "user", "content": "hi"}]})
        assert r.status_code == 400
        assert "key" in r.json()["detail"].lower()
