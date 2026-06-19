-- MCP farm: PostgreSQL + TimescaleDB
-- Multi-tenant, ULID primary keys (application-generated; no UUID defaults).
-- Apply on TimescaleDB (e.g. timescale/timescaledb-ha:pg16).
-- Rationale: docs/AI-aware-zero-trust-gateway-for-MCP.md §7

CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ── Conventions ─────────────────────────────────────────────────────────────
-- ULID: 26-character Crockford base32 (case-insensitive accepted at ingest).
-- All *_id TEXT columns that are PKs or FKs to PKs use ULIDs from the app layer.
-- Tenant isolation: every security-relevant row carries tenant_id → tenants(id).

-- ── Domain helpers ───────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION mcp_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── Tenants ─────────────────────────────────────────────────────────────────

CREATE TABLE tenants (
    id              TEXT NOT NULL,
    slug            TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active'
                        CHECK (status IN ('active', 'suspended', 'closed')),
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_tenants PRIMARY KEY (id),
    CONSTRAINT chk_tenants_id_ulid CHECK (id ~* '^[0-9a-hjkmp-tv-z]{26}$'),
    CONSTRAINT chk_tenants_slug CHECK (slug ~ '^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$')
);

CREATE UNIQUE INDEX uq_tenants_slug_lower ON tenants (lower(slug));

CREATE TRIGGER tr_tenants_updated_at
    BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE PROCEDURE mcp_set_updated_at();

-- ── Platform MCP catalog (shared inventory; not duplicated per tenant) ─────

CREATE TABLE platform_mcp_servers (
    id              TEXT NOT NULL,
    server_key      TEXT NOT NULL,
    image           TEXT NOT NULL,
    port            INTEGER NOT NULL CHECK (port > 0),
    env_template    JSONB NOT NULL DEFAULT '{}'::jsonb,
    status          TEXT NOT NULL DEFAULT 'running'
                        CHECK (status IN ('running', 'stopped', 'starting', 'error')),
    source          TEXT NOT NULL DEFAULT 'static'
                        CHECK (source IN ('static', 'dynamic', 'operator')),
    category        TEXT,
    trust_tier      TEXT NOT NULL DEFAULT 'T1'
                        CHECK (trust_tier IN ('T0', 'T1', 'T2', 'T3')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_health_at  TIMESTAMPTZ,
    health_ok       BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT pk_platform_mcp_servers PRIMARY KEY (id),
    CONSTRAINT chk_platform_mcp_servers_id_ulid CHECK (id ~* '^[0-9a-hjkmp-tv-z]{26}$'),
    CONSTRAINT uq_platform_mcp_servers_key UNIQUE (server_key),
    CONSTRAINT uq_platform_mcp_servers_port UNIQUE (port)
);

CREATE INDEX idx_platform_mcp_servers_status ON platform_mcp_servers (status);
CREATE INDEX idx_platform_mcp_servers_tier ON platform_mcp_servers (trust_tier);

CREATE TRIGGER tr_platform_mcp_servers_updated_at
    BEFORE UPDATE ON platform_mcp_servers
    FOR EACH ROW EXECUTE PROCEDURE mcp_set_updated_at();

-- ── Tenant-scoped overrides for dynamic/registered instances (optional) ─────

CREATE TABLE tenant_mcp_deployments (
    id                      TEXT NOT NULL,
    tenant_id               TEXT NOT NULL,
    platform_mcp_server_id  TEXT REFERENCES platform_mcp_servers (id) ON DELETE SET NULL,
    server_key              TEXT NOT NULL,
    image                   TEXT NOT NULL,
    port                    INTEGER NOT NULL CHECK (port > 0),
    runtime_env             JSONB NOT NULL DEFAULT '{}'::jsonb,
    status                  TEXT NOT NULL DEFAULT 'starting'
                        CHECK (status IN ('running', 'stopped', 'starting', 'error')),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_tenant_mcp_deployments PRIMARY KEY (id),
    CONSTRAINT chk_tenant_mcp_deployments_id_ulid CHECK (id ~* '^[0-9a-hjkmp-tv-z]{26}$'),
    CONSTRAINT fk_tenant_mcp_deployments_tenant
        FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT uq_tenant_mcp_deployments_key UNIQUE (tenant_id, server_key),
    CONSTRAINT uq_tenant_mcp_deployments_port UNIQUE (port)
);

CREATE INDEX idx_tenant_mcp_deployments_tenant ON tenant_mcp_deployments (tenant_id);

CREATE TRIGGER tr_tenant_mcp_deployments_updated_at
    BEFORE UPDATE ON tenant_mcp_deployments
    FOR EACH ROW EXECUTE PROCEDURE mcp_set_updated_at();

-- ── API keys (tenant-scoped; hash is globally unique for O(1) /verify lookup) ─

CREATE TABLE api_keys (
    id              TEXT NOT NULL,
    tenant_id       TEXT NOT NULL,
    key_hash        TEXT NOT NULL,
    key_prefix      TEXT NOT NULL,
    name            TEXT NOT NULL,
    owner_label     TEXT,
    scope_mode      TEXT NOT NULL DEFAULT 'restricted'
                        CHECK (scope_mode IN ('all_platform', 'restricted')),
    rate_limit_rpm  INTEGER NOT NULL DEFAULT 100 CHECK (rate_limit_rpm > 0),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    last_used_at    TIMESTAMPTZ,
    CONSTRAINT pk_api_keys PRIMARY KEY (id),
    CONSTRAINT chk_api_keys_id_ulid CHECK (id ~* '^[0-9a-hjkmp-tv-z]{26}$'),
    CONSTRAINT fk_api_keys_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT uq_api_keys_hash UNIQUE (key_hash),
    CONSTRAINT uq_api_keys_tenant_name UNIQUE (tenant_id, name)
);

CREATE INDEX idx_api_keys_tenant ON api_keys (tenant_id) WHERE is_active = TRUE;
CREATE INDEX idx_api_keys_key_hash ON api_keys (key_hash);

CREATE TRIGGER tr_api_keys_updated_at
    BEFORE UPDATE ON api_keys
    FOR EACH ROW EXECUTE PROCEDURE mcp_set_updated_at();

-- Normalized grants: required when scope_mode = 'restricted' (enforce in app or constraint)

CREATE TABLE api_key_mcp_grants (
    api_key_id              TEXT NOT NULL,
    platform_mcp_server_id  TEXT NOT NULL,
    granted_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_api_key_mcp_grants PRIMARY KEY (api_key_id, platform_mcp_server_id),
    CONSTRAINT fk_api_key_mcp_grants_key
        FOREIGN KEY (api_key_id) REFERENCES api_keys (id) ON DELETE CASCADE,
    CONSTRAINT fk_api_key_mcp_grants_server
        FOREIGN KEY (platform_mcp_server_id) REFERENCES platform_mcp_servers (id) ON DELETE CASCADE
);

CREATE INDEX idx_api_key_mcp_grants_server ON api_key_mcp_grants (platform_mcp_server_id);

-- ── Hypertable: request audit (tenant-partitioned analytics) ────────────────

CREATE TABLE request_log (
    id                      TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tenant_id               TEXT NOT NULL,
    api_key_id              TEXT,
    platform_mcp_server_id  TEXT,
    server_key              TEXT NOT NULL,
    http_method             TEXT,
    http_status             INTEGER,
    latency_ms              INTEGER,
    client_request_id       TEXT,
    CONSTRAINT pk_request_log PRIMARY KEY (id, created_at),
    CONSTRAINT chk_request_log_id_ulid CHECK (id ~* '^[0-9a-hjkmp-tv-z]{26}$'),
    CONSTRAINT fk_request_log_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT fk_request_log_api_key FOREIGN KEY (api_key_id) REFERENCES api_keys (id) ON DELETE SET NULL,
    CONSTRAINT fk_request_log_platform_server
        FOREIGN KEY (platform_mcp_server_id) REFERENCES platform_mcp_servers (id) ON DELETE SET NULL
);

SELECT create_hypertable('request_log', 'created_at', if_not_exists => TRUE);

CREATE INDEX idx_request_log_tenant_created ON request_log (tenant_id, created_at DESC);
CREATE INDEX idx_request_log_key_created ON request_log (api_key_id, created_at DESC)
    WHERE api_key_id IS NOT NULL;
CREATE INDEX idx_request_log_server_key_created ON request_log (server_key, created_at DESC);
CREATE INDEX idx_request_log_platform_created ON request_log (platform_mcp_server_id, created_at DESC)
    WHERE platform_mcp_server_id IS NOT NULL;

-- ── Hypertable: L3 policy / gateway analytics ───────────────────────────────

CREATE TABLE policy_event_log (
    id                      TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    tenant_id               TEXT NOT NULL,
    api_key_id              TEXT,
    server_key              TEXT NOT NULL,
    platform_mcp_server_id  TEXT,
    mcp_method              TEXT,
    tool_name               TEXT,
    policy_action           TEXT NOT NULL
                        CHECK (policy_action IN (
                            'ALLOW', 'ALLOW_WITH_REDACTION', 'REQUIRE_APPROVAL',
                            'DENY', 'QUARANTINE_SESSION', 'ERROR'
                        )),
    policy_reason_code      TEXT,
    latency_ms              INTEGER,
    args_sha256             TEXT,
    client_request_id       TEXT,
    CONSTRAINT pk_policy_event_log PRIMARY KEY (id, created_at),
    CONSTRAINT chk_policy_event_log_id_ulid CHECK (id ~* '^[0-9a-hjkmp-tv-z]{26}$'),
    CONSTRAINT fk_policy_event_log_tenant FOREIGN KEY (tenant_id) REFERENCES tenants (id) ON DELETE CASCADE,
    CONSTRAINT fk_policy_event_log_api_key FOREIGN KEY (api_key_id) REFERENCES api_keys (id) ON DELETE SET NULL,
    CONSTRAINT fk_policy_event_log_platform_server
        FOREIGN KEY (platform_mcp_server_id) REFERENCES platform_mcp_servers (id) ON DELETE SET NULL
);

SELECT create_hypertable('policy_event_log', 'created_at', if_not_exists => TRUE);

CREATE INDEX idx_policy_event_tenant_created ON policy_event_log (tenant_id, created_at DESC);
CREATE INDEX idx_policy_event_key_created ON policy_event_log (api_key_id, created_at DESC)
    WHERE api_key_id IS NOT NULL;
CREATE INDEX idx_policy_event_server_created ON policy_event_log (server_key, created_at DESC);
CREATE INDEX idx_policy_event_action_created ON policy_event_log (policy_action, created_at DESC);

-- ── Row-level security (optional connections: set app.tenant_id for read models) ─
-- Gateway hot path typically uses a role with BYPASSRLS or SECURITY DEFINER for /verify.
-- Enable for analyst / tenant-scoped reporting roles after creating those roles.

-- ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE request_log ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE policy_event_log ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY p_api_keys_tenant ON api_keys FOR ALL
--   USING (tenant_id = current_setting('app.tenant_id', true)::text);
-- CREATE POLICY p_request_log_tenant ON request_log FOR SELECT
--   USING (tenant_id = current_setting('app.tenant_id', true)::text);
-- CREATE POLICY p_policy_event_log_tenant ON policy_event_log FOR SELECT
--   USING (tenant_id = current_setting('app.tenant_id', true)::text);

-- ── Compression / retention (tune per deployment) ─────────────────────────
-- ALTER TABLE request_log SET (
--   timescaledb.compress,
--   timescaledb.compress_segmentby = 'tenant_id, server_key',
--   timescaledb.compress_orderby = 'created_at DESC'
-- );
-- SELECT add_compression_policy('request_log', INTERVAL '7 days');
-- SELECT add_retention_policy('request_log', INTERVAL '400 days');
