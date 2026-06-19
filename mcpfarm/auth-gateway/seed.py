"""
Seed script — idempotent, run via:
    docker compose exec auth-gateway python seed.py

Reads /app/port-map.json and populates the servers table.
Creates a seed-admin API key if one doesn't exist yet.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import secrets
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get("AUTH_DB_PATH", "/data/auth.db")
PORT_MAP_PATH = "/app/port-map.json"


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("""
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
    conn.execute("""
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
    conn.execute("""
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
    conn.commit()


def main() -> None:
    # Load port-map
    with open(PORT_MAP_PATH) as f:
        port_map: dict = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    _init_db(conn)

    now_iso = datetime.utcnow().isoformat()
    seeded_count = 0

    for name, info in port_map.items():
        env_vars = {k: "" for k in info.get("env", [])}
        try:
            conn.execute(
                """INSERT OR IGNORE INTO servers
                   (name, image, port, env, status, source, category, created_at, last_health, health_ok)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    name,
                    info["image"],
                    info["port"],
                    json.dumps(env_vars),
                    "running",
                    "static",
                    info.get("category"),
                    now_iso,
                    None,
                    0,
                ),
            )
            if conn.execute("SELECT changes()").fetchone()[0] > 0:
                seeded_count += 1
        except sqlite3.IntegrityError as e:
            print(f"  SKIP {name}: {e}")

    conn.commit()

    # Check if seed-admin key already exists
    row = conn.execute(
        "SELECT id, key_prefix FROM api_keys WHERE name='seed-admin'"
    ).fetchone()

    plaintext_key = None
    if not row:
        raw = "hd_sk_" + secrets.token_hex(32)
        key_hash = hashlib.sha256(raw.encode()).hexdigest()
        key_prefix = raw[:12]
        key_id = secrets.token_hex(16)
        conn.execute(
            """INSERT INTO api_keys
               (id, key_hash, key_prefix, name, owner, scopes, rate_limit, is_active, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (key_id, key_hash, key_prefix, "seed-admin", "system", "*", 1000, 1, now_iso),
        )
        conn.commit()
        plaintext_key = raw
        # Persist plaintext key so /ui-config can serve it to the UI on first load
        with open("/data/ui-api-key", "w") as kf:
            kf.write(raw)

    conn.close()

    print()
    print("=" * 60)
    print("  HACKERDOGS MCP FARM — SEED COMPLETE")
    print("=" * 60)
    print(f"  Seeded {seeded_count} new servers from port-map.json")
    print(f"  Total servers in port-map: {len(port_map)}")
    if plaintext_key:
        print()
        print("  *** WARNING: SAVE THIS KEY — IT WILL NOT BE SHOWN AGAIN ***")
        print()
        print(f"  Admin API Key: {plaintext_key}")
        print()
        print("  *** WARNING: SAVE THIS KEY — IT WILL NOT BE SHOWN AGAIN ***")
    else:
        print("  seed-admin key already exists — skipping key creation")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
