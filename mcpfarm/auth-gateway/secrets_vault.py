"""
Encrypted storage for LLM provider API keys.

Keys are encrypted with Fernet (AES-128-CBC + HMAC) and stored in the existing
auth-gateway SQLite database. The plaintext key never leaves the server after
it is written; the UI only ever sees a masked prefix.

Master key resolution order:
  1. ``MCPFARM_SECRETS_KEY`` env var (preferred; a url-safe base64 32-byte key).
  2. A persisted key file next to the DB (``<db_dir>/secrets.key``), created
     with 0600 perms on first use so keys survive restarts in dev.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import aiosqlite
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("AUTH_DB_PATH", "/data/auth.db")

# Providers that store a secret API key. (ollama uses a URL, not a secret.)
SECRET_PROVIDERS = {
    "claude", "openai", "bedrock", "azure", "openrouter", "grok", "gemini",
}

_fernet: Optional[Fernet] = None


def _key_file_path() -> str:
    return os.path.join(os.path.dirname(DB_PATH) or ".", "secrets.key")


def _load_or_create_key() -> bytes:
    env_key = os.environ.get("MCPFARM_SECRETS_KEY", "").strip()
    if env_key:
        return env_key.encode()
    path = _key_file_path()
    try:
        with open(path, "rb") as f:
            data = f.read().strip()
            if data:
                return data
    except FileNotFoundError:
        pass
    key = Fernet.generate_key()
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(key)
        logger.warning(
            "MCPFARM_SECRETS_KEY not set; generated a persistent key at %s. "
            "Set MCPFARM_SECRETS_KEY in production.", path,
        )
    except OSError as exc:
        logger.warning("Could not persist secrets key (%s); using ephemeral key", exc)
    return key


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS llm_secrets (
                provider   TEXT PRIMARY KEY,
                ciphertext TEXT NOT NULL,
                key_prefix TEXT,
                updated_at TEXT
            )
            """
        )
        await db.commit()


def _mask(plaintext: str) -> str:
    if not plaintext:
        return ""
    if len(plaintext) <= 8:
        return plaintext[:2] + "…"
    return f"{plaintext[:4]}…{plaintext[-4:]}"


async def set_secret(provider: str, plaintext: str) -> Dict[str, object]:
    provider = provider.lower()
    ciphertext = _get_fernet().encrypt(plaintext.encode()).decode()
    prefix = _mask(plaintext)
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO llm_secrets (provider, ciphertext, key_prefix, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                ciphertext=excluded.ciphertext,
                key_prefix=excluded.key_prefix,
                updated_at=excluded.updated_at
            """,
            (provider, ciphertext, prefix, now),
        )
        await db.commit()
    return {"provider": provider, "key_prefix": prefix, "updated_at": now, "has_key": True}


async def get_secret(provider: str) -> Optional[str]:
    provider = provider.lower()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT ciphertext FROM llm_secrets WHERE provider=?", (provider,)
        ) as cur:
            row = await cur.fetchone()
    if not row:
        return None
    try:
        return _get_fernet().decrypt(row["ciphertext"].encode()).decode()
    except InvalidToken:
        logger.error("Failed to decrypt secret for %s (wrong MCPFARM_SECRETS_KEY?)", provider)
        return None


async def delete_secret(provider: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM llm_secrets WHERE provider=?", (provider.lower(),))
        await db.commit()


async def list_secrets() -> List[Dict[str, object]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT provider, key_prefix, updated_at FROM llm_secrets ORDER BY provider"
        ) as cur:
            rows = await cur.fetchall()
    return [
        {
            "provider": r["provider"],
            "key_prefix": r["key_prefix"],
            "updated_at": r["updated_at"],
            "has_key": True,
        }
        for r in rows
    ]
