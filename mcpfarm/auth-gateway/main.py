"""
Auth-Gateway — FastAPI application providing API key management, forward-auth
verification for Caddy, and dynamic MCP server orchestration.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import secrets
from datetime import datetime
from typing import List, Optional

import aiosqlite
import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

import caddy_reload
import docker_manager
import chat_proxy
import secrets_vault
import vector_index
import vector_indexer
from models import (
    ApiKey,
    KeyCreate,
    KeyResponse,
    KeyUpdate,
    RequestLog,
    Server,
    ServerCreate,
    ServerImport,
    ServerResponse,
)
from rate_limiter import RateLimiter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get("AUTH_DB_PATH", "/data/auth.db")
READMES_ROOT = os.environ.get("READMES_ROOT", "")
if not READMES_ROOT:
    _repo_candidate = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if os.path.isfile(os.path.join(_repo_candidate, "nuclei-mcp", "README.md")):
        READMES_ROOT = _repo_candidate
_SECRET_FILE = "/data/admin-secret"

def _load_admin_secret() -> str:
    try:
        with open(_SECRET_FILE) as f:
            s = f.read().strip()
            if s:
                return s
    except FileNotFoundError:
        pass
    return os.environ.get("ADMIN_SECRET", "")

ADMIN_SECRET = _load_admin_secret()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hackerdogs MCP Auth Gateway", version="1.0.0")
rate_limiter = RateLimiter()

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("PRAGMA synchronous=NORMAL;")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id TEXT PRIMARY KEY,
                key_hash TEXT UNIQUE NOT NULL,
                key_prefix TEXT NOT NULL,
                name TEXT NOT NULL,
                owner TEXT,
                scopes TEXT DEFAULT '*',
                rate_limit INTEGER DEFAULT 100,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                last_used TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                name TEXT PRIMARY KEY,
                image TEXT NOT NULL,
                port INTEGER UNIQUE NOT NULL,
                env TEXT DEFAULT '{}',
                status TEXT DEFAULT 'running',
                source TEXT DEFAULT 'static',
                category TEXT,
                url TEXT,
                created_at TEXT NOT NULL,
                last_health TEXT,
                health_ok INTEGER DEFAULT 0
            )
        """)
        # Migration: add url column if missing (existing DBs)
        try:
            await db.execute("ALTER TABLE servers ADD COLUMN url TEXT")
        except Exception:
            pass
        await db.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_id TEXT NOT NULL,
                server TEXT NOT NULL,
                method TEXT NOT NULL,
                status INTEGER NOT NULL,
                latency_ms INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await db.commit()


def _row_to_dict(row: aiosqlite.Row) -> dict:
    return dict(row)


def _to_key_response(row: dict) -> dict:
    return {
        "id": row["id"],
        "key_prefix": row["key_prefix"],
        "name": row["name"],
        "owner": row.get("owner"),
        "scopes": row["scopes"],
        "rate_limit": row["rate_limit"],
        "is_active": bool(row["is_active"]),
        "created_at": row["created_at"],
        "expires_at": row.get("expires_at"),
        "last_used": row.get("last_used"),
    }


def _to_server_response(row: dict) -> dict:
    return {
        "name": row["name"],
        "image": row["image"],
        "port": row["port"],
        "env": row["env"],
        "status": row["status"],
        "source": row["source"],
        "category": row.get("category"),
        "url": row.get("url"),
        "created_at": row["created_at"],
        "last_health": row.get("last_health"),
        "health_ok": bool(row.get("health_ok", False)),
    }


async def _next_available_port() -> int:
    """Find the next available port starting from 9000."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT port FROM servers ORDER BY port DESC LIMIT 1") as cur:
            row = await cur.fetchone()
            max_port = row[0] if row else 8999
    return max(9000, max_port + 1)


# ---------------------------------------------------------------------------
# Background health check
# ---------------------------------------------------------------------------

async def _probe_mcp_server(client: httpx.AsyncClient, name: str, port: int) -> bool:
    """Return True if the MCP server process is accepting HTTP.

    Proxy-based servers expose GET /health → 200. Native FastMCP (streamable-http)
    servers have no /health route but respond on GET /mcp/ with 4xx (< 500).
    """
    health_resp = await client.get(f"http://{name}:{port}/health")
    if health_resp.status_code == 200:
        return True
    mcp_resp = await client.get(f"http://{name}:{port}/mcp/")
    # 404 on /mcp/ means a proxy that only serves /health (and is not healthy).
    if mcp_resp.status_code == 404:
        return False
    return mcp_resp.status_code < 500


async def _check_one(name: str, port: int, url: str | None = None) -> tuple[str, bool]:
    """Probe a single MCP server without spawning an MCP session."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            if url:
                health_url = url.rstrip("/")
                if not health_url.endswith("/health"):
                    health_url = health_url.rsplit("/", 1)[0] + "/health" if "/" in health_url.split("//", 1)[-1] else health_url + "/health"
                resp = await client.get(health_url)
                if resp.status_code == 200:
                    return name, True
                # Custom URL may point at a proxy; fall through to /mcp/ only when needed.
                base = health_url.rsplit("/health", 1)[0].rstrip("/")
                mcp_resp = await client.get(f"{base}/mcp/")
                if mcp_resp.status_code == 404:
                    return name, False
                return name, mcp_resp.status_code < 500
            ok = await _probe_mcp_server(client, name, port)
            return name, ok
    except Exception:
        return name, False


async def health_check_loop() -> None:
    """Periodically check health of all registered MCP servers (concurrent, max 40 at a time)."""
    sem = asyncio.Semaphore(40)

    async def bounded_check(name: str, port: int, url: str | None = None) -> tuple[str, bool]:
        async with sem:
            return await _check_one(name, port, url)

    while True:
        await asyncio.sleep(30)
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT name, port, url FROM servers") as cursor:
                    servers = await cursor.fetchall()

            results = await asyncio.gather(
                *[bounded_check(srv["name"], srv["port"], srv.get("url")) for srv in servers],
                return_exceptions=True,
            )

            now = datetime.utcnow().isoformat()
            async with aiosqlite.connect(DB_PATH) as db:
                for result in results:
                    if isinstance(result, Exception):
                        continue
                    name, ok = result
                    await db.execute(
                        "UPDATE servers SET health_ok=?, last_health=? WHERE name=?",
                        (1 if ok else 0, now, name),
                    )
                await db.commit()
        except Exception as exc:
            logger.error("Health check error: %s", exc)


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup_event() -> None:
    await init_db()

    # Ensure /data/ui-api-key exists so the UI can authenticate MCP requests
    if not os.path.exists("/data/ui-api-key"):
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            row = await db.execute_fetchall(
                "SELECT key_hash FROM api_keys WHERE name='seed-admin' AND is_active=1"
            )
        if row:
            raw = "hd_sk_" + secrets.token_hex(32)
            key_hash = hashlib.sha256(raw.encode()).hexdigest()
            key_id = secrets.token_hex(16)
            now_iso = datetime.utcnow().isoformat()
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    """INSERT INTO api_keys
                       (id, key_hash, key_prefix, name, owner, scopes, rate_limit, is_active, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (key_id, key_hash, raw[:12], "ui-auto", "system", "*", 1000, 1, now_iso),
                )
                await db.commit()
            with open("/data/ui-api-key", "w") as kf:
                kf.write(raw)
            logger.info("Created ui-auto API key for UI authentication")

    # Recover dynamic servers
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM servers WHERE source='dynamic'"
        ) as cursor:
            dynamic_rows = await cursor.fetchall()

    class _Srv:
        def __init__(self, row):
            self.name = row["name"]
            self.image = row["image"]
            self.port = row["port"]
            self.env = row["env"]
            try:
                self.url = row["url"]
            except (IndexError, KeyError):
                self.url = None

    dynamic_servers = [_Srv(r) for r in dynamic_rows]
    if dynamic_servers:
        # Run in thread pool — Docker SDK calls are synchronous and would block the event loop
        loop = asyncio.get_event_loop()
        asyncio.create_task(
            loop.run_in_executor(None, docker_manager.recover_dynamic_servers, dynamic_servers)
        )

    # Push Caddy config — retry until Caddy admin API is ready
    async def _reload_caddy_with_retry():
        for attempt in range(15):
            await asyncio.sleep(3)
            try:
                await _reload_caddy_from_db()
                return
            except Exception:
                pass
        logger.warning("Caddy reload failed after all retries")
    asyncio.create_task(_reload_caddy_with_retry())

    # Initialize the encrypted LLM-key vault table.
    try:
        await secrets_vault.init_db()
    except Exception as exc:  # noqa: BLE001
        logger.warning("secrets_vault init failed: %s", exc)

    # Ensure the Redis vector index exists (best-effort; hd-redis is shared).
    async def _ensure_vectors():
        try:
            if await vector_index.ping():
                await vector_index.ensure_index()
                logger.info("Redis vector index ready (%s)", vector_index.INDEX_NAME)
                if os.environ.get("VECTOR_AUTO_REINDEX", "").lower() in ("1", "true", "yes"):
                    await _reindex_vectors()
            else:
                logger.warning("Redis not reachable at %s; vector search disabled", vector_index.REDIS_URL)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Vector index init failed: %s", exc)
    asyncio.create_task(_ensure_vectors())

    # Start background health check
    asyncio.create_task(health_check_loop())
    logger.info("Auth-gateway started. DB: %s", DB_PATH)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------

async def require_admin(request: Request) -> None:
    secret = request.headers.get("X-Admin-Secret", "")
    if not secret or secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden: invalid admin secret")


async def require_api_key(request: Request) -> None:
    """Validate a Bearer API key (active, non-expired) — used by chat/vector routes."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token_hash = hashlib.sha256(auth_header[len("Bearer "):].encode()).hexdigest()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT is_active, expires_at FROM api_keys WHERE key_hash=?", (token_hash,)
        ) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not row["is_active"]:
        raise HTTPException(status_code=403, detail="API key is inactive")
    if row["expires_at"]:
        try:
            if datetime.utcnow() > datetime.fromisoformat(row["expires_at"]):
                raise HTTPException(status_code=403, detail="API key has expired")
        except ValueError:
            pass


@app.post("/admin/rotate-secret", dependencies=[Depends(require_admin)])
async def rotate_admin_secret():
    """Generate a new admin secret, persist it, and return it."""
    global ADMIN_SECRET
    new_secret = secrets.token_hex(32)
    with open(_SECRET_FILE, "w") as f:
        f.write(new_secret)
    ADMIN_SECRET = new_secret
    # Also update ui-api-key file so /ui-config stays consistent
    try:
        with open("/data/ui-api-key") as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        api_key = None
    return {"admin_secret": new_secret, "api_key": api_key}


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ui-config")
async def ui_config():
    """Returns UI bootstrap config — API key + admin secret, no auth required."""
    api_key = None
    try:
        with open("/data/ui-api-key") as f:
            api_key = f.read().strip()
    except FileNotFoundError:
        pass
    return {"base_url": "", "api_key": api_key, "admin_secret": ADMIN_SECRET}


@app.get("/services")
async def list_services():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers") as cursor:
            rows = await cursor.fetchall()
    return [_to_server_response(dict(r)) for r in rows]


def _readme_path(server_name: str) -> Optional[str]:
    """Resolve README.md for an MCP server directory."""
    if not READMES_ROOT:
        return None
    name = server_name if server_name.endswith("-mcp") else f"{server_name}-mcp"
    path = os.path.join(READMES_ROOT, name, "README.md")
    if os.path.isfile(path):
        return path
    return None


@app.get("/services/{name}/readme")
async def get_server_readme(name: str):
    path = _readme_path(name)
    if not path:
        raise HTTPException(status_code=404, detail="README not found")
    with open(path, encoding="utf-8", errors="replace") as f:
        return PlainTextResponse(f.read(), media_type="text/markdown; charset=utf-8")


@app.get("/verify")
async def verify(request: Request):
    """Forward-auth endpoint called by Caddy for every MCP request."""
    import time

    start = time.time()

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    raw_token = auth_header[len("Bearer "):]
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            "SELECT * FROM api_keys WHERE key_hash=?", (token_hash,)
        ) as cursor:
            row = await cursor.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid API key")

        key = dict(row)
        if not key["is_active"]:
            raise HTTPException(status_code=403, detail="API key is inactive")

        if key["expires_at"]:
            try:
                exp = datetime.fromisoformat(key["expires_at"])
                if datetime.utcnow() > exp:
                    raise HTTPException(status_code=403, detail="API key has expired")
            except ValueError:
                pass

        # Extract server name from forwarded URI (first path segment)
        forwarded_uri = request.headers.get("X-Forwarded-Uri", "/")
        parts = forwarded_uri.strip("/").split("/")
        server_name = parts[0] if parts else ""

        # Check scopes
        scopes = key["scopes"]
        if scopes != "*" and server_name not in scopes.split(","):
            raise HTTPException(status_code=403, detail="Insufficient scope")

        # Rate limiting
        allowed = await rate_limiter.check(key["id"], key["rate_limit"])
        if not allowed:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        # Update last_used
        now_iso = datetime.utcnow().isoformat()
        await db.execute(
            "UPDATE api_keys SET last_used=? WHERE id=?",
            (now_iso, key["id"]),
        )

        # Log request
        latency_ms = int((time.time() - start) * 1000)
        method = request.headers.get("X-Forwarded-Method", "GET")
        await db.execute(
            """INSERT INTO request_logs (key_id, server, method, status, latency_ms, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (key["id"], server_name, method, 200, latency_ms, now_iso),
        )
        await db.commit()

    return Response(status_code=200)


# ---------------------------------------------------------------------------
# Admin: API key endpoints
# ---------------------------------------------------------------------------

@app.post("/admin/keys", dependencies=[Depends(require_admin)])
async def create_key(payload: KeyCreate):
    raw = "hd_sk_" + secrets.token_hex(32)
    key_hash = hashlib.sha256(raw.encode()).hexdigest()
    key_prefix = raw[:12]
    key_id = secrets.token_hex(16)
    now_iso = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO api_keys (id, key_hash, key_prefix, name, owner, scopes, rate_limit,
               is_active, created_at, expires_at, last_used)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                key_id, key_hash, key_prefix, payload.name, payload.owner,
                payload.scopes, payload.rate_limit, 1, now_iso,
                payload.expires_at.isoformat() if payload.expires_at else None,
                None,
            ),
        )
        await db.commit()

    return {
        "id": key_id,
        "key": raw,  # Returned ONCE in plaintext
        "key_prefix": key_prefix,
        "name": payload.name,
        "owner": payload.owner,
        "scopes": payload.scopes,
        "rate_limit": payload.rate_limit,
        "created_at": now_iso,
    }


@app.get("/admin/keys", dependencies=[Depends(require_admin)])
async def list_keys():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM api_keys") as cursor:
            rows = await cursor.fetchall()
    return [_to_key_response(dict(r)) for r in rows]


@app.get("/admin/keys/{key_id}", dependencies=[Depends(require_admin)])
async def get_key(key_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM api_keys WHERE id=?", (key_id,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Key not found")
    return _to_key_response(dict(row))


@app.patch("/admin/keys/{key_id}", dependencies=[Depends(require_admin)])
async def update_key(key_id: str, payload: KeyUpdate):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM api_keys WHERE id=?", (key_id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Key not found")

        updates = {}
        if payload.scopes is not None:
            updates["scopes"] = payload.scopes
        if payload.rate_limit is not None:
            updates["rate_limit"] = payload.rate_limit
        if payload.is_active is not None:
            updates["is_active"] = 1 if payload.is_active else 0
        if payload.expires_at is not None:
            updates["expires_at"] = payload.expires_at.isoformat()

        if updates:
            set_clause = ", ".join(f"{k}=?" for k in updates)
            values = list(updates.values()) + [key_id]
            await db.execute(
                f"UPDATE api_keys SET {set_clause} WHERE id=?", values
            )
            await db.commit()

        async with db.execute("SELECT * FROM api_keys WHERE id=?", (key_id,)) as cursor:
            updated = await cursor.fetchone()
    return _to_key_response(dict(updated))


@app.delete("/admin/keys/{key_id}", dependencies=[Depends(require_admin)])
async def delete_key(key_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id FROM api_keys WHERE id=?", (key_id,)) as cursor:
            row = await cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Key not found")
        await db.execute("DELETE FROM api_keys WHERE id=?", (key_id,))
        await db.commit()
    return {"deleted": key_id}


@app.get("/admin/keys/{key_id}/usage", dependencies=[Depends(require_admin)])
async def key_usage(key_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT server, COUNT(*) as count FROM request_logs WHERE key_id=? GROUP BY server",
            (key_id,),
        ) as cursor:
            rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Admin: server endpoints
# ---------------------------------------------------------------------------

@app.post("/admin/servers", dependencies=[Depends(require_admin)])
async def create_server(payload: ServerCreate):
    now_iso = datetime.utcnow().isoformat()
    env_json = json.dumps(payload.env)
    is_external = bool(payload.url)
    port = payload.port if payload.port else await _next_available_port()
    source = "external" if is_external else "dynamic"
    status = "running" if is_external else "starting"

    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                """INSERT INTO servers (name, image, port, env, status, source, category, url,
                   created_at, last_health, health_ok)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (payload.name, payload.image or "", port, env_json,
                 status, source, payload.category, payload.url, now_iso, None, 0),
            )
            await db.commit()
        except Exception as exc:
            if "UNIQUE" in str(exc).upper() or "IntegrityError" in type(exc).__name__:
                raise HTTPException(status_code=409, detail=f"Server '{payload.name}' already exists")
            raise

    if not is_external:
        try:
            docker_manager.start_server(payload.name, payload.image, port, payload.env)
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE servers SET status='running' WHERE name=?", (payload.name,)
                )
                await db.commit()
        except Exception as exc:
            logger.error("Failed to start container %s: %s", payload.name, exc)
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "UPDATE servers SET status='error' WHERE name=?", (payload.name,)
                )
                await db.commit()

    await _reload_caddy_from_db()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (payload.name,)) as cursor:
            row = await cursor.fetchone()
    return _to_server_response(dict(row))


@app.post("/admin/servers/import", dependencies=[Depends(require_admin)])
async def import_servers(payload: ServerImport):
    """Import MCP servers from Claude Desktop or Cursor JSON config format."""
    results = []
    for name, config in payload.mcpServers.items():
        server_name = name if name.endswith("-mcp") else f"{name}-mcp"
        server_name = server_name.lower().replace(" ", "-").replace("_", "-")

        async with aiosqlite.connect(DB_PATH) as db:
            async with db.execute("SELECT name FROM servers WHERE name=?", (server_name,)) as cur:
                if await cur.fetchone():
                    results.append({"name": server_name, "status": "skipped", "reason": "already exists"})
                    continue

        url = config.get("url")
        command = config.get("command", "")
        args = config.get("args", [])
        env = config.get("env", {})
        category = config.get("category")

        if url:
            sc = ServerCreate(name=server_name, url=url, env=env, category=category)
        elif command == "docker" and args:
            image = next((a for a in args if "/" in a and ":" in a or not a.startswith("-")), "")
            image = image.strip()
            if not image:
                image = args[-1] if args else ""
            sc = ServerCreate(name=server_name, image=image, env=env, category=category)
        elif command in ("npx", "node", "npm"):
            pkg = ""
            skip_next = False
            for a in args:
                if skip_next:
                    skip_next = False
                    continue
                if a in ("-y", "--yes", "exec", "run"):
                    continue
                if a.startswith("-"):
                    if a in ("-p", "--package"):
                        skip_next = True
                    continue
                pkg = a
                break
            image = f"hackerdogs/{server_name}:latest"
            sc = ServerCreate(name=server_name, image=image, env=env, category=category)
        else:
            results.append({"name": server_name, "status": "skipped", "reason": f"unsupported command: {command}"})
            continue

        try:
            resp = await create_server(sc)
            results.append({"name": server_name, "status": "created", "server": resp})
        except Exception as exc:
            results.append({"name": server_name, "status": "error", "reason": str(exc)})

    return {"imported": len([r for r in results if r["status"] == "created"]), "results": results}


@app.get("/admin/servers", dependencies=[Depends(require_admin)])
async def list_servers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers") as cursor:
            rows = await cursor.fetchall()
    return [_to_server_response(dict(r)) for r in rows]


# ---------------------------------------------------------------------------
# Automation API — static routes (must be before /admin/servers/{name})
# ---------------------------------------------------------------------------


class BatchAction(BaseModel):
    servers: List[str] = []
    action: str


@app.post("/admin/servers/batch", dependencies=[Depends(require_admin)])
async def batch_server_action(payload: BatchAction):
    """Run start/stop/restart/enable/disable on multiple servers at once."""
    allowed = {"start", "stop", "restart", "enable", "disable"}
    if payload.action not in allowed:
        raise HTTPException(status_code=400, detail=f"action must be one of {sorted(allowed)}")

    handler_map = {
        "start": start_server_endpoint,
        "stop": stop_server_endpoint,
        "restart": restart_server_endpoint,
        "enable": enable_server_endpoint,
        "disable": disable_server_endpoint,
    }
    handler = handler_map[payload.action]
    results = []
    for name in payload.servers:
        try:
            resp = await handler(name)
            results.append({"name": name, "status": "ok", "result": resp})
        except HTTPException as exc:
            results.append({"name": name, "status": "error", "detail": exc.detail})
        except Exception as exc:
            results.append({"name": name, "status": "error", "detail": str(exc)})
    return {"action": payload.action, "total": len(results), "results": results}


@app.post("/admin/servers/health-check", dependencies=[Depends(require_admin)])
async def batch_health_check(names: Optional[List[str]] = None):
    """Health-check all servers (or a subset). Returns per-server results."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        if names:
            placeholders = ",".join("?" for _ in names)
            query = f"SELECT name, port, status FROM servers WHERE name IN ({placeholders})"
            async with db.execute(query, names) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute("SELECT name, port, status FROM servers") as cursor:
                rows = await cursor.fetchall()

    async def _check_one_health(row):
        name = row["name"]
        port = row["port"]
        if row["status"] in ("stopped", "disabled"):
            return {"name": name, "healthy": False, "reason": row["status"]}
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                ok = await _probe_mcp_server(client, name, port)
            return {"name": name, "healthy": ok}
        except Exception:
            return {"name": name, "healthy": False, "reason": "unreachable"}

    results = await asyncio.gather(*[_check_one_health(r) for r in rows])
    healthy = sum(1 for r in results if r["healthy"])
    return {"total": len(results), "healthy": healthy, "unhealthy": len(results) - healthy, "results": list(results)}


@app.get("/admin/servers/search", dependencies=[Depends(require_admin)])
async def search_servers(
    q: Optional[str] = Query(default=None, description="Name substring match"),
    category: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    healthy: Optional[bool] = Query(default=None),
):
    """Filter servers by name, category, status, source, or health."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        clauses = []
        params: list = []
        if q:
            clauses.append("name LIKE ?")
            params.append(f"%{q}%")
        if category:
            clauses.append("category = ?")
            params.append(category)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if source:
            clauses.append("source = ?")
            params.append(source)
        if healthy is not None:
            clauses.append("health_ok = ?")
            params.append(1 if healthy else 0)

        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        async with db.execute(f"SELECT * FROM servers{where}", params) as cursor:
            rows = await cursor.fetchall()
    return {"count": len(rows), "servers": [_to_server_response(dict(r)) for r in rows]}


@app.get("/admin/servers/categories", dependencies=[Depends(require_admin)])
async def list_categories():
    """List all distinct server categories with counts."""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT category, COUNT(*) as count FROM servers GROUP BY category ORDER BY count DESC"
        ) as cursor:
            rows = await cursor.fetchall()
    return {"categories": [{"category": r[0] or "uncategorized", "count": r[1]} for r in rows]}


# ---------------------------------------------------------------------------
# Admin: single-server endpoints (parameterized routes)
# ---------------------------------------------------------------------------

@app.get("/admin/servers/{name}", dependencies=[Depends(require_admin)])
async def get_server(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    return _to_server_response(dict(row))


@app.delete("/admin/servers/{name}", dependencies=[Depends(require_admin)])
async def delete_server(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")

    srv = dict(row)
    if srv.get("source") != "external":
        try:
            docker_manager.stop_server(name)
        except Exception as exc:
            logger.warning("Could not stop container %s: %s", name, exc)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM servers WHERE name=?", (name,))
        await db.commit()

    await _reload_caddy_from_db()
    return {"deleted": name}


@app.patch("/admin/servers/{name}/env", dependencies=[Depends(require_admin)])
async def update_server_env(name: str, request: Request):
    """Update env vars for a server. Pass a flat JSON object of key→value pairs."""
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")

    # Merge new values into existing env (preserves keys not in body)
    existing_env = json.loads(dict(row).get("env") or "{}")
    existing_env.update(body)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE servers SET env=? WHERE name=?",
            (json.dumps(existing_env), name),
        )
        await db.commit()

    return {"name": name, "env": existing_env}


@app.post("/admin/servers/{name}/restart", dependencies=[Depends(require_admin)])
async def restart_server_endpoint(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    srv = dict(row)
    env_vars = json.loads(srv["env"]) if srv["env"] else {}
    env_vars.pop("MCP_TRANSPORT", None)
    env_vars.pop("MCP_PORT", None)
    try:
        docker_manager.restart_server(name, srv["image"], srv["port"], env_vars)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE servers SET status='running' WHERE name=?", (name,)
            )
            await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"restarted": name}


@app.post("/admin/servers/{name}/start", dependencies=[Depends(require_admin)])
async def start_server_endpoint(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    srv = dict(row)
    env_vars = json.loads(srv["env"]) if srv["env"] else {}
    env_vars.pop("MCP_TRANSPORT", None)
    env_vars.pop("MCP_PORT", None)
    try:
        docker_manager.start_server(name, srv["image"], srv["port"], env_vars)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE servers SET status='running' WHERE name=?", (name,)
            )
            await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    # Probe health in background after a short delay so the first UI poll finds it ready
    asyncio.create_task(_probe_health_after_start(name, srv["port"]))
    return {"started": name}


async def _probe_health_after_start(name: str, port: int) -> None:
    """Retry health probe every 3s for up to 45s after a server is started."""
    for attempt in range(15):
        await asyncio.sleep(3)
        _, ok = await _check_one(name, port)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE servers SET health_ok=?, last_health=? WHERE name=?",
                (1 if ok else 0, datetime.utcnow().isoformat(), name),
            )
            await db.commit()
        if ok:
            # Index this server's tools + mark running in the vector store.
            asyncio.create_task(_vector_index_server_safe(name))
            break


@app.post("/admin/servers/{name}/stop", dependencies=[Depends(require_admin)])
async def stop_server_endpoint(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    try:
        docker_manager.stop_server(name)
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                "UPDATE servers SET status='stopped', health_ok=0, last_health=? WHERE name=?",
                (datetime.utcnow().isoformat(), name),
            )
            await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    asyncio.create_task(_vector_set_status_safe(name, "stopped"))
    return {"stopped": name}


@app.post("/admin/servers/{name}/enable", dependencies=[Depends(require_admin)])
async def enable_server_endpoint(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    srv = dict(row)
    new_status = "running" if srv.get("health_ok") else "stopped"
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE servers SET status=? WHERE name=?", (new_status, name)
        )
        await db.commit()
    await _reload_caddy_from_db()
    return {"enabled": name, "status": new_status}


@app.post("/admin/servers/{name}/disable", dependencies=[Depends(require_admin)])
async def disable_server_endpoint(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE servers SET status='disabled' WHERE name=?", (name,)
        )
        await db.commit()
    await _reload_caddy_from_db()
    asyncio.create_task(_vector_set_status_safe(name, "disabled"))
    return {"disabled": name}


@app.get("/admin/servers/{name}/health", dependencies=[Depends(require_admin)])
async def server_health(name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT port FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    port = row["port"]
    ok = False
    status_code = 0
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            ok = await _probe_mcp_server(client, name, port)
            resp = await client.get(f"http://{name}:{port}/mcp/")
            status_code = resp.status_code
    except Exception:
        status_code = -1

    now_iso = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE servers SET health_ok=?, last_health=? WHERE name=?",
            (1 if ok else 0, now_iso, name),
        )
        await db.commit()

    return {"name": name, "healthy": ok, "status_code": status_code, "checked_at": now_iso}


@app.get("/admin/servers/{name}/tools", dependencies=[Depends(require_admin)])
async def get_server_tools(name: str):
    """List MCP tools exposed by a running server."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    srv = dict(row)
    try:
        tools = await _load_tools_for_server(srv)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch tools: {exc}")
    return {"server": name, "tools": tools or [], "count": len(tools or [])}


@app.get("/admin/servers/{name}/logs", dependencies=[Depends(require_admin)])
async def server_logs(name: str, tail: int = Query(default=100)):
    logs = docker_manager.get_logs(name, tail=tail)
    return {"name": name, "logs": logs}


# ---------------------------------------------------------------------------
# Admin: farm-wide endpoints
# ---------------------------------------------------------------------------

@app.get("/admin/stats", dependencies=[Depends(require_admin)])
async def farm_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT COUNT(*) as c FROM api_keys") as cur:
            total_keys = (await cur.fetchone())["c"]
        async with db.execute("SELECT COUNT(*) as c FROM api_keys WHERE is_active=1") as cur:
            active_keys = (await cur.fetchone())["c"]
        async with db.execute("SELECT COUNT(*) as c FROM servers") as cur:
            total_servers = (await cur.fetchone())["c"]
        async with db.execute("SELECT COUNT(*) as c FROM servers WHERE health_ok=1") as cur:
            healthy_servers = (await cur.fetchone())["c"]
        async with db.execute("SELECT COUNT(*) as c FROM request_logs") as cur:
            total_requests = (await cur.fetchone())["c"]

    return {
        "total_keys": total_keys,
        "active_keys": active_keys,
        "total_servers": total_servers,
        "healthy_servers": healthy_servers,
        "total_requests": total_requests,
    }


@app.get("/admin/audit", dependencies=[Depends(require_admin)])
async def audit_log(
    key_id: Optional[str] = Query(default=None),
    server: Optional[str] = Query(default=None),
    since: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100),
):
    conditions = []
    params = []
    if key_id:
        conditions.append("key_id=?")
        params.append(key_id)
    if server:
        conditions.append("server=?")
        params.append(server)
    if since:
        conditions.append("created_at>=?")
        params.append(since.isoformat())

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    params.append(limit)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT * FROM request_logs {where} ORDER BY created_at DESC LIMIT ?",
            params,
        ) as cursor:
            rows = await cursor.fetchall()
    return [dict(r) for r in rows]


@app.post("/admin/reload", dependencies=[Depends(require_admin)])
async def reload_routes():
    await _reload_caddy_from_db()
    return {"status": "reloaded"}


@app.get("/admin/export", dependencies=[Depends(require_admin)])
async def export_farm():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers") as cursor:
            servers = [dict(r) for r in await cursor.fetchall()]
        async with db.execute("SELECT * FROM api_keys") as cursor:
            keys_raw = [dict(r) for r in await cursor.fetchall()]

    # Strip key_hash from export
    keys = [_to_key_response(k) for k in keys_raw]
    return {"servers": servers, "keys": keys}


# ---------------------------------------------------------------------------
# Claude API proxy — avoids browser CORS restrictions
# ---------------------------------------------------------------------------

@app.post("/claude")
async def claude_proxy(request: Request):
    """Proxy Claude API calls from the UI to avoid CORS issues.

    The API key is taken from the encrypted vault; the legacy ``x-claude-key``
    header is still accepted as a fallback for backward compatibility.
    """
    body = await request.body()
    claude_key = request.headers.get("x-claude-key", "")
    anthropic_version = request.headers.get("anthropic-version", "2023-06-01")

    if not claude_key:
        claude_key = await secrets_vault.get_secret("claude") or ""

    if not claude_key:
        return JSONResponse(
            {"error": "No Claude API key configured. Add it in Settings."},
            status_code=400,
        )

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            content=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": claude_key,
                "anthropic-version": anthropic_version,
            },
        )

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type="application/json",
    )


# ---------------------------------------------------------------------------
# Chat completions proxy (keys decrypted server-side)
# ---------------------------------------------------------------------------

class ChatCompletionRequest(BaseModel):
    provider: str
    model: Optional[str] = None
    messages: List[dict] = []
    tools: List[dict] = []
    max_tokens: int = 4096


@app.post("/chat/completions", dependencies=[Depends(require_api_key)])
async def chat_completions(req: ChatCompletionRequest):
    try:
        return await chat_proxy.run_completion(req.model_dump())
    except chat_proxy.ChatProxyError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("chat_completions failed")
        raise HTTPException(status_code=502, detail=str(exc))


# ---------------------------------------------------------------------------
# Vector search (dynamic tool binding)
# ---------------------------------------------------------------------------

class VectorSearchRequest(BaseModel):
    query: str
    mode: str = "dynamic"
    filters: dict = {}
    top_k_servers: int = 5
    top_k_tools: int = 20
    min_score: float = 0.0


@app.post("/vectors/search", dependencies=[Depends(require_api_key)])
async def vectors_search(req: VectorSearchRequest):
    import embeddings

    if not await vector_index.ping():
        raise HTTPException(status_code=503, detail="Vector store unavailable")
    if not await vector_index.index_exists():
        raise HTTPException(status_code=503, detail="Vector index not built; run /admin/vectors/reindex")

    statuses = None
    status_filter = (req.filters or {}).get("status")
    if status_filter:
        statuses = [status_filter] if isinstance(status_filter, str) else list(status_filter)
    categories = (req.filters or {}).get("categories") or None

    query_vec = await embeddings.embed_text(req.query)

    # Stage 1 — server discovery over server/alias/readme docs.
    stage1 = await vector_index.search_knn(
        query_vec,
        top_k=max(req.top_k_servers * 4, 12),
        doc_types=["server", "alias", "readme"],
        statuses=statuses,
        categories=categories,
    )
    server_order: List[str] = []
    for row in stage1:
        srv = row.get("server")
        if srv and srv not in server_order:
            server_order.append(srv)
        if len(server_order) >= req.top_k_servers:
            break

    # Stage 2 — rank tools within the discovered servers.
    tools: List[dict] = []
    if server_order:
        stage2 = await vector_index.search_knn(
            query_vec,
            top_k=req.top_k_tools,
            doc_types=["tool"],
            servers=server_order,
            statuses=statuses,
        )
        for row in stage2:
            sim = row.get("similarity")
            if sim is not None and sim < req.min_score:
                continue
            tools.append({
                "server": row.get("server"),
                "tool": row.get("tool"),
                "description": row.get("text"),
                "score": row.get("similarity"),
            })

    return {
        "mode": req.mode,
        "servers": server_order,
        "tools": tools,
        "meta": {"stage1": len(stage1), "returned_tools": len(tools)},
    }


# ---------------------------------------------------------------------------
# LLM key vault (admin)
# ---------------------------------------------------------------------------

class LlmKeyUpsert(BaseModel):
    key: str


@app.get("/llm-keys", dependencies=[Depends(require_admin)])
async def list_llm_keys():
    return {"keys": await secrets_vault.list_secrets(), "providers": sorted(secrets_vault.SECRET_PROVIDERS)}


@app.put("/llm-keys/{provider}", dependencies=[Depends(require_admin)])
async def put_llm_key(provider: str, payload: LlmKeyUpsert):
    if provider.lower() not in secrets_vault.SECRET_PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    if not payload.key.strip():
        raise HTTPException(status_code=400, detail="Empty key")
    return await secrets_vault.set_secret(provider, payload.key.strip())


@app.delete("/llm-keys/{provider}", dependencies=[Depends(require_admin)])
async def delete_llm_key(provider: str):
    await secrets_vault.delete_secret(provider)
    return {"status": "deleted", "provider": provider.lower()}


# ---------------------------------------------------------------------------
# Vector index admin
# ---------------------------------------------------------------------------

def _read_readme(server_name: str) -> Optional[str]:
    path = _readme_path(server_name)
    if not path:
        return None
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


async def _load_tools_for_server(srv: dict) -> List[dict]:
    name = srv.get("name")
    port = srv.get("port")
    if not name or not port:
        return []
    return await vector_indexer.list_tools_internal(name, int(port))


async def _reindex_vectors() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers") as cursor:
            servers = [dict(r) for r in await cursor.fetchall()]
    return await vector_indexer.reindex_all(servers, _read_readme, _load_tools_for_server)


async def _vector_set_status_safe(name: str, status: str) -> None:
    """Best-effort: flip a server's status tag in the vector index."""
    try:
        if await vector_index.ping() and await vector_index.index_exists():
            await vector_index.set_server_status(name, status)
    except Exception as exc:  # noqa: BLE001
        logger.debug("vector status update failed for %s: %s", name, exc)


async def _vector_index_server_safe(name: str) -> None:
    """Best-effort: (re)index a single running server's tools + metadata."""
    try:
        if not (await vector_index.ping() and await vector_index.index_exists()):
            return
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
                row = await cursor.fetchone()
        if not row:
            return
        srv = dict(row)
        status = vector_indexer._status_of(srv)
        tools = None
        if status == "running":
            try:
                tools = await _load_tools_for_server(srv)
            except Exception:  # noqa: BLE001
                tools = None
        await vector_indexer.index_server(name, srv.get("category"), status, _read_readme(name), tools)
    except Exception as exc:  # noqa: BLE001
        logger.debug("vector index-server failed for %s: %s", name, exc)


@app.post("/admin/vectors/reindex", dependencies=[Depends(require_admin)])
async def admin_vectors_reindex():
    if not await vector_index.ping():
        raise HTTPException(status_code=503, detail="Vector store unavailable")
    return await _reindex_vectors()


@app.get("/admin/vectors/stats", dependencies=[Depends(require_admin)])
async def admin_vectors_stats():
    return await vector_index.stats()


@app.post("/admin/vectors/index-server/{name}", dependencies=[Depends(require_admin)])
async def admin_vectors_index_server(name: str):
    if not await vector_index.ping():
        raise HTTPException(status_code=503, detail="Vector store unavailable")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (name,)) as cursor:
            row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Server not found")
    srv = dict(row)
    status = vector_indexer._status_of(srv)
    tools = None
    if status == "running":
        try:
            tools = await _load_tools_for_server(srv)
        except Exception as exc:  # noqa: BLE001
            logger.warning("index-server %s tools failed: %s", name, exc)
    n = await vector_indexer.index_server(name, srv.get("category"), status, _read_readme(name), tools)
    return {"server": name, "docs": n, "status": status, "tools": len(tools or [])}




# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _reload_caddy_from_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT name, port FROM servers WHERE status != 'disabled'"
        ) as cursor:
            rows = await cursor.fetchall()

    class _Srv:
        def __init__(self, row):
            self.name = row["name"]
            self.port = row["port"]
            try:
                self.url = row["url"]
            except (IndexError, KeyError):
                self.url = None

    servers = [_Srv(r) for r in rows]
    await caddy_reload.write_and_reload(servers)
