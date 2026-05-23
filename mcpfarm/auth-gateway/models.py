"""
SQLModel database models and Pydantic request/response schemas for the auth-gateway.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


# ---------------------------------------------------------------------------
# Database tables
# ---------------------------------------------------------------------------

class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: str = Field(default_factory=lambda: secrets.token_hex(16), primary_key=True)
    key_hash: str = Field(unique=True, index=True)
    key_prefix: str
    name: str
    owner: Optional[str] = Field(default=None)
    scopes: str = Field(default="*")
    rate_limit: int = Field(default=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
    last_used: Optional[datetime] = Field(default=None)


class Server(SQLModel, table=True):
    __tablename__ = "servers"

    name: str = Field(primary_key=True)
    image: str
    port: int = Field(unique=True)
    env: str = Field(default="{}")
    status: str = Field(default="running")
    source: str = Field(default="static")
    category: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_health: Optional[datetime] = Field(default=None)
    health_ok: bool = Field(default=False)


class RequestLog(SQLModel, table=True):
    __tablename__ = "request_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    key_id: str = Field(foreign_key="api_keys.id")
    server: str
    method: str
    status: int
    latency_ms: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# Pydantic request/response schemas
# ---------------------------------------------------------------------------

class KeyCreate(BaseModel):
    name: str
    owner: Optional[str] = None
    scopes: str = "*"
    rate_limit: int = 100
    expires_at: Optional[datetime] = None


class KeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    owner: Optional[str]
    scopes: str
    rate_limit: int
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]

    class Config:
        from_attributes = True


class KeyUpdate(BaseModel):
    scopes: Optional[str] = None
    rate_limit: Optional[int] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class ServerCreate(BaseModel):
    name: str
    image: str
    port: int
    env: Dict[str, str] = {}
    category: Optional[str] = None


class ServerResponse(BaseModel):
    name: str
    image: str
    port: int
    env: str
    status: str
    source: str
    category: Optional[str]
    created_at: datetime
    last_health: Optional[datetime]
    health_ok: bool

    class Config:
        from_attributes = True
