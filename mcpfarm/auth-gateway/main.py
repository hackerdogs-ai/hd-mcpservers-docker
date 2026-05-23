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
from fastapi.responses import JSONResponse

import caddy_reload
import docker_manager
from models import (
    ApiKey,
    KeyCreate,
    KeyResponse,
    KeyUpdate,
    RequestLog,
    Server,
    ServerCreate,
    ServerResponse,
)
from rate_limiter import RateLimiter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DB_PATH = os.environ.get("AUTH_DB_PATH", "/data/auth.db")
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
                created_at TEXT NOT NULL,
                last_health TEXT,
                health_ok INTEGER DEFAULT 0
            )
        """)
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
        "created_at": row["created_at"],
        "last_health": row.get("last_health"),
        "health_ok": bool(row.get("health_ok", False)),
    }


# ---------------------------------------------------------------------------
# Background health check
# ---------------------------------------------------------------------------

async def _check_one(name: str, port: int) -> tuple[str, bool]:
    """Probe a single MCP server; returns (name, ok)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"http://{name}:{port}/mcp",
                json={"jsonrpc": "2.0", "id": 0, "method": "initialize",
                      "params": {"protocolVersion": "2024-11-05",
                                 "capabilities": {},
                                 "clientInfo": {"name": "health", "version": "1"}}},
                headers={"Content-Type": "application/json",
                         "Accept": "application/json, text/event-stream"},
            )
            return name, resp.status_code < 500
    except Exception:
        return name, False


async def health_check_loop() -> None:
    """Periodically check health of all registered MCP servers (concurrent, max 40 at a time)."""
    sem = asyncio.Semaphore(40)

    async def bounded_check(name: str, port: int) -> tuple[str, bool]:
        async with sem:
            return await _check_one(name, port)

    while True:
        await asyncio.sleep(30)
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute("SELECT name, port FROM servers") as cursor:
                    servers = await cursor.fetchall()

            results = await asyncio.gather(
                *[bounded_check(srv["name"], srv["port"]) for srv in servers],
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

    dynamic_servers = [_Srv(r) for r in dynamic_rows]
    if dynamic_servers:
        # Run in thread pool — Docker SDK calls are synchronous and would block the event loop
        loop = asyncio.get_event_loop()
        asyncio.create_task(
            loop.run_in_executor(None, docker_manager.recover_dynamic_servers, dynamic_servers)
        )

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

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO servers (name, image, port, env, status, source, category, created_at,
               last_health, health_ok)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (payload.name, payload.image, payload.port, env_json,
             "starting", "dynamic", payload.category, now_iso, None, 0),
        )
        await db.commit()

    # Start container
    try:
        docker_manager.start_server(payload.name, payload.image, payload.port, payload.env)
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

    # Reload Caddy routes
    await _reload_caddy_from_db()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers WHERE name=?", (payload.name,)) as cursor:
            row = await cursor.fetchone()
    return _to_server_response(dict(row))


@app.get("/admin/servers", dependencies=[Depends(require_admin)])
async def list_servers():
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM servers") as cursor:
            rows = await cursor.fetchall()
    return [_to_server_response(dict(r)) for r in rows]


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
                "UPDATE servers SET status='stopped' WHERE name=?", (name,)
            )
            await db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"stopped": name}


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
            resp = await client.get(f"http://{name}:{port}/mcp/")
            status_code = resp.status_code
            ok = status_code < 500
    except Exception as exc:
        status_code = -1

    now_iso = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE servers SET health_ok=?, last_health=? WHERE name=?",
            (1 if ok else 0, now_iso, name),
        )
        await db.commit()

    return {"name": name, "healthy": ok, "status_code": status_code, "checked_at": now_iso}


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
# Internal helpers
# ---------------------------------------------------------------------------

async def _reload_caddy_from_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT name, port FROM servers") as cursor:
            rows = await cursor.fetchall()

    class _Srv:
        def __init__(self, row):
            self.name = row["name"]
            self.port = row["port"]

    servers = [_Srv(r) for r in rows]
    await caddy_reload.write_and_reload(servers)
