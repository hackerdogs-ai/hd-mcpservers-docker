# Technical Spec: Multi-Instance MCP Servers in the Farm

> **Status:** Draft / Proposal
> **Scope:** Allow a single logical MCP server (e.g. `crawl4ai-mcp`) to run as **N horizontally-scaled replicas** behind one farm endpoint, with health, routing, session affinity, and lifecycle managed by the auth-gateway.
> **Related docs:** [FARM-PRD.md](./FARM-PRD.md), [FARM-ARCHITECTURE.md](./FARM-ARCHITECTURE.md), [AI-aware zero-trust gateway for MCP](./AI-aware-zero-trust-gateway-for-MCP.md)

---

## Part 1 — Product Requirements (PRD)

### 1.1 Problem statement

Today the farm enforces a strict **1:1:1:1 mapping** — one logical server name maps to exactly one database row, one internal port, one Docker container, and one Caddy route. There is no concept of "replicas" or "scale". A user who needs throughput beyond what a single container of, say, `crawl4ai-mcp` can provide has no first-class way to run 20 instances behind a shared endpoint.

The identity chain that binds everything to a single instance:

| Layer | Where | Constraint today |
|-------|-------|------------------|
| DB row | `servers.name` | `PRIMARY KEY` — one row per name |
| Port | `servers.port` | `UNIQUE NOT NULL` — one port per name |
| Container | `docker_manager.start_server(name=name)` | Docker container names are globally unique |
| DNS / upstream | Caddy `reverse_proxy {name}:{port}` | Resolves name to one container |
| Route | Caddy `path /{name}/*` | One URL path per name |

Current container creation even **force-removes** any existing container with the same name, so a naive "start again" replaces rather than scales:

```37:43:mcpfarm/auth-gateway/docker_manager.py
    # Remove any existing container with the same name
    try:
        existing = client.containers.get(name)
        logger.info("Removing existing container %s ...", name)
        existing.remove(force=True)
    except docker.errors.NotFound:
        pass
```

### 1.2 Goals

| # | Goal |
|---|------|
| G1 | A logical server can declare a **desired replica count** (`1..N`). |
| G2 | All replicas are reachable through a **single, unchanged endpoint** (`/{name}/mcp`) — clients need no awareness of replicas. |
| G3 | Requests are **load-balanced** across healthy replicas. |
| G4 | **MCP session affinity**: all requests for a given `mcp-session-id` reach the replica that created that session (stateful correctness). |
| G5 | **Per-replica health**; the logical server is "running" if **≥1 replica is healthy**. |
| G6 | Scale up/down at runtime via the **admin API** and the **farm UI**, without restarting the compose stack. |
| G7 | **Backward compatible**: existing single-instance servers keep working with zero migration effort (`desired_replicas` defaults to `1`). |
| G8 | Survive an **auth-gateway restart** — replicas are recovered/reconciled to desired state. |

### 1.3 Non-goals

- Cross-host / multi-node orchestration (Swarm, Kubernetes). This spec targets the single Docker Engine the farm already uses. K8s is noted as a future path only.
- Autoscaling based on live load metrics. Scaling is **explicit** (operator sets a count). Metrics-driven autoscaling is a future extension.
- Shared persistent state between replicas of a server (e.g. a shared file workspace). See risk R4; addressed via session affinity, not shared volumes.
- Changing the auth model (Bearer token + `/verify` forward-auth) — reused unchanged.

### 1.4 Users & stories

- **Farm operator**: "I set `crawl4ai-mcp` to 20 replicas and the farm runs 20 containers behind `/crawl4ai-mcp/mcp`, load-balanced, and I can scale back to 3 later."
- **MCP client / LLM**: "I connect to the same URL as always; I don't know or care how many replicas exist. My session keeps working across calls."
- **On-call**: "One replica crashed; the endpoint stays up on the surviving replicas, and the dashboard shows 19/20 healthy."

### 1.5 Functional requirements

| ID | Requirement |
|----|-------------|
| FR1 | `desired_replicas: int ≥ 1` is a property of a logical server. |
| FR2 | The gateway reconciles running replica containers to `desired_replicas`. |
| FR3 | Each replica is an independent container named deterministically (`{name}-{index}`). |
| FR4 | Caddy routes `/{name}/*` to the set of healthy replica upstreams. |
| FR5 | Session-affinity ensures `mcp-session-id` → same replica for the session's lifetime. |
| FR6 | New-session (initialize) requests are distributed across healthy replicas. |
| FR7 | `/services` returns aggregated logical status **and** a per-replica breakdown. |
| FR8 | Admin endpoints: set replica count, list instances, restart/stop a single instance. |
| FR9 | UI shows replica count, per-replica health, and a scale control. |
| FR10 | On gateway boot, replicas with `source != external` are reconciled to desired state. |

### 1.6 Success metrics

- Setting `crawl4ai-mcp` to N spins up N healthy containers within the existing health-probe window (≤45s per replica) and the endpoint serves traffic across all of them.
- Throughput scales roughly linearly with replica count for stateless tool calls (bounded by host resources).
- Zero client-side changes required (same URL, same Bearer token).
- A single replica failure does not take the endpoint down (graceful degradation to `N-1`).

---

## Part 2 — Current-State Analysis

### 2.1 Data model (single-instance)

The `servers` table (mirrored in `models.py` and `seed.py`) keys on `name` and forces a unique `port`:

```35:48:mcpfarm/auth-gateway/models.py
class Server(SQLModel, table=True):
    __tablename__ = "servers"

    name: str = Field(primary_key=True)
    image: str
    port: int = Field(unique=True)
    env: str = Field(default="{}")
    status: str = Field(default="running")
    source: str = Field(default="static")
    category: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_health: Optional[datetime] = Field(default=None)
    health_ok: bool = Field(default=False)
```

### 2.2 Container lifecycle

`start_server` creates exactly one container named `name`, on `mcpfarm_internal`, with `MCP_TRANSPORT`/`MCP_PORT` injected, and **no host port binding** (internal DNS only):

```52:61:mcpfarm/auth-gateway/docker_manager.py
    container = client.containers.run(
        image=image,
        name=name,
        detach=True,
        environment=env,
        network=network,
        restart_policy={"Name": "unless-stopped"},
        # No host port bindings — internal network only
    )
```

> **Key insight:** because access is by Docker DNS name (`crawl4ai-mcp:8521`) and there is **no host port binding**, replicas can **share the same internal port** — each container has a distinct DNS name (`crawl4ai-mcp-1:8521`, `crawl4ai-mcp-2:8521`, …). The global `port UNIQUE` constraint is an artifact of the single-instance model, not a networking requirement.

### 2.3 Routing (one upstream per name)

Caddy generates one route block per server, pointing at a single upstream:

```86:96:mcpfarm/auth-gateway/caddy_reload.py
    return (
        f"    @{name} path /{name}/*\n"
        f"    handle @{name} {{\n"
        f"        forward_auth auth-gateway:9090 {{\n"
        f"            uri /verify\n"
        f"            copy_headers Authorization\n"
        f"        }}\n"
        f"        uri strip_prefix /{name}\n"
        f"        reverse_proxy {name}:{port}\n"
        f"    }}"
    )
```

### 2.4 Auth & scoping keyed on the path's first segment

`/verify` derives the server name from the first path segment and checks scope against it — so a **single pooled path** (`/crawl4ai-mcp/*`) keeps auth/scoping unchanged:

```442:450:mcpfarm/auth-gateway/main.py
        # Extract server name from forwarded URI (first path segment)
        forwarded_uri = request.headers.get("X-Forwarded-Uri", "/")
        parts = forwarded_uri.strip("/").split("/")
        server_name = parts[0] if parts else ""

        # Check scopes
        scopes = key["scopes"]
        if scopes != "*" and server_name not in scopes.split(","):
            raise HTTPException(status_code=403, detail="Insufficient scope")
```

### 2.5 Health model

Health is per-name today. `_probe_mcp_server` tries `/health` then `/mcp/`; a background loop refreshes every 30s and `_probe_health_after_start` polls 15×3s after a start. The UI treats a server as running only when `health_ok === true`:

```62:66:mcpfarm-ui/src/lib/categories.js
export function isServerRunning(server) {
  if (!server) return false;
  const s = (server.status || '').toLowerCase();
  if (s === 'disabled' || s === 'stopped') return false;
  return server.health_ok === true;
}
```

### 2.6 MCP session statefulness (the crux)

MCP Streamable HTTP is **stateful**: the server issues an `mcp-session-id` on `initialize`, and that session lives on the specific process that created it. The UI client keys sessions per server and, on HTTP 404, **re-initializes**:

```62:68:mcpfarm-ui/src/lib/mcp.js
    if (!res.ok) {
      // Spec: 404 + session ID => session terminated; clear and re-init once.
      if (retryOn404 && res.status === 404 && sessionId) {
        this.resetSession(serverName);
        await this.initialize(serverName);
        return this._post(serverName, body, this.sessions[serverName], { retryOn404: false });
      }
```

**Implication:** if a load balancer sends session X to a replica that did not create X, that replica returns 404, the client re-initializes, and state (e.g. an in-progress crawl, a downloaded file) is lost. Therefore **session affinity is a correctness requirement, not an optimization** (FR5).

---

## Part 3 — Proposed Architecture

### 3.1 Concepts

- **Logical server**: the existing `servers` row (e.g. `crawl4ai-mcp`). Becomes a *template + desired state*: image, env, category, `desired_replicas`.
- **Instance (replica)**: a new first-class entity — one container of a logical server, named `{name}-{index}` (e.g. `crawl4ai-mcp-1`). Tracked in a new `server_instances` table.
- **Pool**: the set of healthy instances for a logical server; the routing target.

```
                          ┌───────────────────────────────────────┐
                          │            auth-gateway                 │
   client ── Bearer ──▶ Caddy ── /verify ──▶ (authorize + scope)    │
                          │      reconcile loop ──▶ Docker SDK       │
                          └───────────────────────────────────────┘
                                    │ routes /crawl4ai-mcp/* to pool
                                    ▼
        ┌───────────────┬───────────────┬─────────────── … ──────────────┐
        ▼               ▼               ▼                                 ▼
  crawl4ai-mcp-1   crawl4ai-mcp-2   crawl4ai-mcp-3      ...        crawl4ai-mcp-20
   :8521            :8521            :8521                          :8521
  (same internal port; distinct Docker DNS names on mcpfarm_internal)
```

### 3.2 Two-phase delivery

Because session affinity is the hard part, delivery is split:

- **Phase 1 — Replica management (no shared endpoint).** Add instances, scaling, per-instance health, and reconciliation. Expose each replica on its own route (`/crawl4ai-mcp-1/*`, …). This delivers horizontal capacity immediately with **no LB correctness risk**, useful when clients can be pinned to distinct instances. Low complexity.
- **Phase 2 — Pooled endpoint with session affinity.** Introduce a single `/crawl4ai-mcp/*` endpoint that load-balances across replicas with sticky sessions. This is the full realization of G2–G4 and is the recommended end state.

The data model and reconciliation from Phase 1 are reused wholesale by Phase 2.

---

## Part 4 — Data Model Changes

### 4.1 New column on `servers`

```sql
ALTER TABLE servers ADD COLUMN desired_replicas INTEGER NOT NULL DEFAULT 1;
```

Semantics: number of replica containers the gateway should keep running for this logical server when it is not `stopped`/`disabled`.

### 4.2 New table `server_instances`

```sql
CREATE TABLE IF NOT EXISTS server_instances (
    id             TEXT PRIMARY KEY,          -- "{server_name}-{index}", e.g. crawl4ai-mcp-3
    server_name    TEXT NOT NULL,             -- FK -> servers.name
    instance_index INTEGER NOT NULL,          -- 1..N, stable per logical server
    container_name TEXT UNIQUE NOT NULL,      -- Docker container name (== id)
    port           INTEGER NOT NULL,          -- internal port (may equal template port for all replicas)
    status         TEXT NOT NULL DEFAULT 'starting',  -- starting|running|stopped|error
    health_ok      INTEGER NOT NULL DEFAULT 0,
    last_health    TEXT,
    created_at     TEXT NOT NULL,
    UNIQUE (server_name, instance_index),
    FOREIGN KEY (server_name) REFERENCES servers(name) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_instances_server ON server_instances(server_name);
```

Notes:
- `port` is **no longer globally unique** at the instance level (replicas share the template port). Keep the `servers.port` column as the *template/default port* but drop reliance on its `UNIQUE` guarantee once the instance table is authoritative (see migration 4.4).
- `status`/`health_ok` move to a per-instance grain. The logical server's `servers.health_ok` becomes a **derived aggregate** (any healthy instance ⇒ true).

### 4.3 New table `session_affinity` (Phase 2)

```sql
CREATE TABLE IF NOT EXISTS session_affinity (
    session_id   TEXT PRIMARY KEY,   -- mcp-session-id issued by a replica
    server_name  TEXT NOT NULL,
    instance_id  TEXT NOT NULL,      -- FK -> server_instances.id
    created_at   TEXT NOT NULL,
    last_seen    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_affinity_instance ON session_affinity(instance_id);
```

Used only by the session-aware router (Phase 2, §6.2). Entries are pruned when a session 404s or an instance is removed.

### 4.4 Migration & backfill (idempotent, on gateway startup)

1. `ALTER TABLE servers ADD COLUMN desired_replicas INTEGER NOT NULL DEFAULT 1` (guarded by a `PRAGMA table_info` check).
2. Create `server_instances` and `session_affinity` if absent.
3. **Backfill**: for every existing `servers` row with `source != 'external'` and no instance rows, insert one instance:
   - `id = container_name = name`  (matches the *current* container name, so no container churn on upgrade)
   - `instance_index = 1`
   - `port = servers.port`, `status = servers.status`, `health_ok = servers.health_ok`
4. Leave `servers.port UNIQUE` in place for now (existing single instances still satisfy it). New replicas (`index ≥ 2`) live only in `server_instances`, which does **not** impose global port uniqueness.

> Backfilling instance #1 to the **existing** container name (`crawl4ai-mcp`, not `crawl4ai-mcp-1`) is deliberate: upgrading the gateway must not stop/rename running containers. New naming (`{name}-{index}`) applies to replicas #2+ and to any server whose count is later changed. A one-time "normalize names" admin action (optional) can migrate #1 to `-1` during a maintenance window.

---

## Part 5 — Docker Manager Changes

### 5.1 Instance-aware primitives

Replace name-centric calls with instance-centric ones. Add Docker **labels** so instances are discoverable/recoverable without relying solely on the DB.

```python
# docker_manager.py (proposed)

LABEL_SERVER = "mcpfarm.server"
LABEL_INDEX = "mcpfarm.instance"

def start_instance(container_name, server_name, index, image, port, env_vars,
                   network="mcpfarm_internal"):
    client = _get_client()
    _ensure_image(client, image)
    _remove_if_exists(client, container_name)     # only this specific container
    env = {"MCP_TRANSPORT": "streamable-http", "MCP_PORT": str(port), **env_vars}
    client.containers.run(
        image=image,
        name=container_name,
        detach=True,
        environment=env,
        network=network,
        restart_policy={"Name": "unless-stopped"},
        labels={LABEL_SERVER: server_name, LABEL_INDEX: str(index)},
    )

def stop_instance(container_name):
    ...  # stop + remove that container only

def list_instances(server_name=None):
    filters = {"label": f"{LABEL_SERVER}={server_name}"} if server_name else {"label": LABEL_SERVER}
    return _get_client().containers.list(all=True, filters=filters)
```

The existing `start_server`/`stop_server`/`restart_server` become thin wrappers over the instance primitives for `index=1`, preserving current call sites during migration.

### 5.2 Reconciliation

A pure function computes the delta between desired and actual, and the gateway applies it:

```python
async def reconcile_server(server_row):
    if server_row["source"] == "external":
        return
    if server_row["status"] in ("stopped", "disabled"):
        desired = 0
    else:
        desired = max(1, server_row["desired_replicas"])

    current = await get_instance_rows(server_row["name"])          # from DB
    running = {c.name for c in docker_manager.list_instances(server_row["name"])}

    # 1. Start missing indices 1..desired
    for idx in range(1, desired + 1):
        cname = f"{server_row['name']}-{idx}" if idx > 1 or _use_indexed(server_row) else server_row["name"]
        if cname not in running:
            docker_manager.start_instance(cname, server_row["name"], idx,
                                          server_row["image"], server_row["port"], env_of(server_row))
            upsert_instance_row(cname, server_row["name"], idx, server_row["port"], "starting")

    # 2. Stop surplus indices > desired
    for inst in current:
        if inst["instance_index"] > desired:
            docker_manager.stop_instance(inst["container_name"])
            delete_instance_row(inst["id"])

    await _reload_caddy_from_db()
```

`reconcile_server` is invoked on: scale change, start/stop/enable/disable, and once per logical server on **gateway startup** (replacing `recover_dynamic_servers`).

---

## Part 6 — Routing & Load Balancing

### 6.1 Phase 1 — one route per instance

`generate_route_block` is extended to emit a block per **instance**. For `crawl4ai-mcp` at N=3 this yields `/crawl4ai-mcp-1/*`, `/crawl4ai-mcp-2/*`, `/crawl4ai-mcp-3/*`, each `reverse_proxy {container_name}:{port}`. Auth/scoping continue to key on the path's first segment (§2.4). Simple, correct, but the client must choose an instance.

### 6.2 Phase 2 — pooled route with session affinity (recommended)

Expose a single `/{name}/*` that targets all healthy replicas. Two candidate mechanisms:

#### Option A — Caddy-native load balancing (simplest, limited affinity)

```
@crawl4ai-mcp path /crawl4ai-mcp/*
handle @crawl4ai-mcp {
    forward_auth auth-gateway:9090 { uri /verify; copy_headers Authorization }
    uri strip_prefix /crawl4ai-mcp
    reverse_proxy crawl4ai-mcp-1:8521 crawl4ai-mcp-2:8521 crawl4ai-mcp-3:8521 {
        lb_policy cookie mcp_upstream       # stickiness via Set-Cookie
        lb_retries 2
        health_uri /mcp/
        health_status 2xx 4xx
    }
}
```

**Limitation:** Caddy's `header`-based hashing does **not** guarantee affinity to the *creating* replica (the `initialize` request has no session id yet, so the creator is chosen independently of the later hash target — see §2.6). Caddy's `cookie` policy works only if the MCP client returns the cookie; the farm's `mcp.js` uses `fetch` without sending cookies, so Option A alone is **insufficient for correctness** with the current client.

#### Option B — Gateway-mediated sticky proxy (recommended, correct)

Route pooled traffic **through the auth-gateway**, which already authorizes every request, and let it own affinity:

```
@crawl4ai-mcp path /crawl4ai-mcp/*
handle @crawl4ai-mcp {
    forward_auth auth-gateway:9090 { uri /verify; copy_headers Authorization }
    uri strip_prefix /crawl4ai-mcp
    reverse_proxy auth-gateway:9090      # gateway proxies to the chosen replica
}
```

New gateway proxy handler `/{name}/mcp` logic:

1. Read `mcp-session-id` header.
2. **If present** and found in `session_affinity` → forward to that instance; refresh `last_seen`.
3. **If absent** (initialize) → pick a healthy instance by **least-active-sessions** (or round-robin), forward, and on the response **capture the `mcp-session-id`** the replica returns; write `session_affinity(session_id → instance_id)`.
4. **On 404 from a replica** for a known session → delete the affinity row and let the client re-initialize (matches existing `mcp.js` 404 recovery).
5. Stream the response (SSE `text/event-stream`) transparently — the gateway must not buffer MCP streaming responses.

This is the only option that guarantees FR4–FR6 with the current client and keeps the public contract (`/{name}/mcp`) unchanged.

> **Trade-off:** Option B puts the gateway on the data path for pooled servers (not just auth). Mitigate by (a) using async streaming passthrough, (b) keeping single-instance servers on the direct Caddy path (no proxy hop), and (c) allowing a per-server flag `routing_mode = direct | pooled`.

### 6.3 Health gating of upstreams

Only `health_ok = 1` instances are emitted into the pool. `reload_caddy` / the gateway router filters instances by health so a crashed replica is removed from rotation (G5). Aggregated `servers.health_ok = OR(instance.health_ok)`.

---

## Part 7 — Health Checks (per-instance)

- Generalize `_check_one` / `_probe_mcp_server` to accept an **instance** (`container_name`, `port`) instead of a logical name.
- Background loop iterates `server_instances` (bounded concurrency, reuse the existing semaphore of 40).
- After a scale-up, run `_probe_health_after_start` **per new instance**.
- After each cycle, recompute and persist the aggregate `servers.health_ok`.

```python
async def _refresh_aggregate_health(server_name, db):
    row = await db.execute_fetchone(
        "SELECT MAX(health_ok) AS any_ok FROM server_instances WHERE server_name=?",
        (server_name,))
    await db.execute("UPDATE servers SET health_ok=?, last_health=? WHERE name=?",
                     (1 if row["any_ok"] else 0, now_iso(), server_name))
```

---

## Part 8 — API Changes

### 8.1 New / changed admin endpoints

| Method | Path | Body / Query | Behavior |
|--------|------|--------------|----------|
| `PATCH` | `/admin/servers/{name}/scale` | `{ "replicas": 20 }` | Set `desired_replicas`, then `reconcile_server`. Validates `1 ≤ replicas ≤ MAX_REPLICAS`. |
| `GET` | `/admin/servers/{name}/instances` | — | List instance rows (index, container, port, status, health). |
| `POST` | `/admin/servers/{name}/instances/{index}/restart` | — | Restart one replica. |
| `POST` | `/admin/servers/{name}/instances/{index}/stop` | — | Stop one replica (does not change `desired_replicas`; reconcile may restart it — see §8.3). |
| `GET` | `/admin/servers/{name}/instances/{index}/logs` | `?tail=` | Per-replica logs. |

### 8.2 Changed response shapes

`GET /services` and `GET /admin/servers/{name}` gain:

```json
{
  "name": "crawl4ai-mcp",
  "status": "running",
  "health_ok": true,
  "desired_replicas": 20,
  "ready_replicas": 19,
  "instances": [
    { "index": 1, "container": "crawl4ai-mcp",   "port": 8521, "status": "running", "health_ok": true },
    { "index": 2, "container": "crawl4ai-mcp-2", "port": 8521, "status": "running", "health_ok": true },
    { "index": 3, "container": "crawl4ai-mcp-3", "port": 8521, "status": "error",   "health_ok": false }
  ]
}
```

`ServerResponse` (Pydantic) adds `desired_replicas`, `ready_replicas`, and `instances: List[InstanceResponse]`. Existing fields are unchanged, so old clients keep working (G7).

### 8.3 Semantics: manual stop vs. desired state

A single-instance stop is transient by design (reconciliation restores desired count). To take a replica out of rotation durably, either (a) reduce `desired_replicas`, or (b) mark the instance `disabled` (new instance-level status that reconciliation respects). This spec uses `desired_replicas` as the single source of truth and treats per-instance stop as a **restart-on-next-reconcile** unless the instance is explicitly `disabled`.

### 8.4 `create_server` / scaling interaction

`create_server` (`main.py`) accepts an optional `desired_replicas` (default 1). Port assignment via `_next_available_port` still applies to the **template** port; replicas reuse it. `ServerCreate` gains `desired_replicas: int = 1`.

---

## Part 9 — UI Changes (`mcpfarm-ui`)

- **Server detail** (`ServerDetail.jsx`): add a **Replicas** control (numeric stepper + "Apply") calling `PATCH /admin/servers/{name}/scale`; render an **Instances** table (index, health dot, status, restart/logs actions) fed by the new `instances[]`.
- **`isServerRunning`** (`categories.js`): unchanged — it already reads the aggregate `health_ok`, which now means "≥1 replica healthy".
- **Polling**: reuse the existing 3s×15 post-action poll; additionally show `ready_replicas / desired_replicas` (e.g. "19/20 ready") so a partial scale-up is visible instead of an opaque "Working…".
- **List/Marketplace** (`ServerList.jsx`, `Marketplace.jsx`): add a small "×N" badge when `desired_replicas > 1`.
- **MCP client** (`mcp.js`): **no change** — it keeps hitting `/{name}/mcp`; affinity is handled server-side (Phase 2, §6.2).

---

## Part 10 — Startup, Recovery, Compose

- On boot, the gateway loads all non-external servers and calls `reconcile_server` for each, replacing `recover_dynamic_servers`. This restarts missing replicas and prunes surplus containers left over from a previous desired count.
- `docker-compose.yml` static service blocks remain valid for `index=1`. Servers scaled beyond 1 are managed **dynamically** by the gateway (compose does not know about `-2..-N`); this matches how dynamic servers already work today.
- `seed.py`: extend `_init_db` to create the two new tables and the `desired_replicas` column so a fresh DB is born multi-instance-capable; seeding sets `desired_replicas` from an optional `port-map.json` field (default 1):

```json
"crawl4ai-mcp": {
  "port": 8521,
  "image": "hackerdogs/crawl4ai-mcp:latest",
  "category": "core",
  "replicas": 1,
  "env": ["CRAWL4AI_URL", "CRAWL4AI_API_TOKEN"]
}
```

---

## Part 11 — Configuration

| Setting | Default | Purpose |
|---------|---------|---------|
| `MAX_REPLICAS` (env) | `20` | Hard cap per logical server to protect the host. |
| `FARM_MAX_TOTAL_CONTAINERS` (env) | `200` | Global guardrail across all servers. |
| `routing_mode` (per server) | `direct` | `direct` = one upstream (today); `pooled` = gateway sticky router (§6.2). Auto-set to `pooled` when `desired_replicas > 1`. |
| health cadence | `30s` (existing) | Reused; now per-instance. |

---

## Part 12 — Rollout Plan

1. **Migration-only release**: add columns/tables + backfill instance #1. No behavior change. Verify all existing servers still healthy.
2. **Phase 1**: instance primitives, reconciliation, per-instance health, scale API, per-instance routes, UI replica table. Ship behind `routing_mode=direct` (per-instance routes).
3. **Phase 2**: gateway sticky proxy + `session_affinity`, pooled `/{name}/*` route, `routing_mode=pooled`. Roll out on one server (`crawl4ai-mcp`) first, validate affinity, then enable broadly.
4. **Cleanup (optional)**: normalize instance #1 container name to `-1`, drop `servers.port UNIQUE` once instances are authoritative.

Each phase is independently revertible; the feature is gated by `desired_replicas` (staying at `1` reproduces today's behavior exactly).

---

## Part 13 — Testing Strategy

- **Unit**: `reconcile_server` delta math (scale up, down, no-op, from-zero); container-name derivation; aggregate-health computation; affinity pick/store/prune.
- **Integration (Docker)**: scale `crawl4ai-mcp` 1→3→1; assert container count, `instances[]`, and aggregate health; kill one replica and assert it is removed from the pool then reconciled back.
- **Session-affinity correctness (Phase 2)**: `initialize` → capture session id → issue N follow-up calls → assert **all** land on the creating replica (assert via a per-replica marker, e.g. `INSTANCE_INDEX` env echoed by a debug tool or gleaned from logs). Then kill that replica → assert 404 → client re-init lands on a survivor.
- **Load**: concurrent sessions across replicas; verify roughly even initialize distribution and stable per-session routing.
- **Backward-compat**: a fresh single-instance server behaves identically to today (`desired_replicas=1`, direct route, same URL).
- **Restart recovery**: bounce the gateway with a server at N=5; assert 5 replicas reconciled on boot.

---

## Part 14 — Risks & Mitigations

| ID | Risk | Mitigation |
|----|------|------------|
| R1 | **Session affinity gap** — LB sends a session to the wrong replica → 404 churn, lost state. | Phase 2 Option B (gateway-owned `session_affinity`); never rely on Caddy hash alone. |
| R2 | **Resource exhaustion** — 20× containers overwhelm the host. | `MAX_REPLICAS`, `FARM_MAX_TOTAL_CONTAINERS`, and (future) per-container CPU/mem limits in `start_instance`. |
| R3 | **Gateway on data path** (Option B) becomes a bottleneck / SSE buffering bug. | Async streaming passthrough; keep single-instance servers on the direct path; load-test streaming. |
| R4 | **Instance-local state** — e.g. `gitleaks`/`crawl4ai` write files to a container FS; a follow-up call on another replica can't see them. | Session affinity keeps a client's calls on one replica; document that cross-replica shared workspaces are out of scope; optionally add a shared volume per server where semantically safe. |
| R5 | **Caddy reload race** during rapid scaling. | Debounce `_reload_caddy_from_db`; reconcile computes final desired set then reloads once. |
| R6 | **Port-uniqueness assumptions** elsewhere in code. | Instances share the template port (allowed — distinct DNS names); audit `_next_available_port` and `port UNIQUE` usages; keep uniqueness only for the template row until §12.4 cleanup. |
| R7 | **Thundering health herd** at high replica counts. | Reuse bounded-concurrency semaphore; jitter per-instance probe start. |
| R8 | **Name collisions** if an operator manually creates `crawl4ai-mcp-2`. | Reserve the `{name}-{int}` suffix pattern; validate on `create_server`. |

---

## Part 15 — Future Extensions

- **Metrics-driven autoscaling** (scale on request rate / queue depth from `request_logs`).
- **Multi-node** via Docker Swarm or Kubernetes (`Deployment` + `Service` naturally model replicas; this spec's logical/instance split maps cleanly onto it).
- **Weighted / canary** replicas (route a % to a new image tag).
- **Per-replica resource quotas** and **graceful drain** (stop routing new sessions to a replica, wait for existing sessions to end, then remove).

---

## Appendix A — Affected Files

| File | Change |
|------|--------|
| `mcpfarm/auth-gateway/models.py` | `Server.desired_replicas`; new `ServerInstance`, `SessionAffinity` models; extended `ServerResponse`. |
| `mcpfarm/auth-gateway/seed.py` | Create new tables + column; seed `replicas` from `port-map.json`. |
| `mcpfarm/auth-gateway/docker_manager.py` | `start_instance`/`stop_instance`/`list_instances`, labels; `reconcile` support. |
| `mcpfarm/auth-gateway/main.py` | `reconcile_server`; scale/instances endpoints; per-instance health; pooled sticky proxy (Phase 2); aggregate health; startup reconcile. |
| `mcpfarm/auth-gateway/caddy_reload.py` | Per-instance / pooled route generation; health-gated upstreams. |
| `mcpfarm-ui/src/lib/api.js` | `scaleServer`, `listInstances`, per-instance restart/stop/logs. |
| `mcpfarm-ui/src/components/ServerDetail.jsx` | Replica control + instances table + `ready/desired` progress. |
| `mcpfarm-ui/src/components/ServerList.jsx`, `Marketplace.jsx` | `×N` badge. |
| `mcpfarm/port-map.json` | Optional `replicas` field per server. |

## Appendix B — Worked Example: `crawl4ai-mcp` → 20

1. Operator sets replicas: `PATCH /admin/servers/crawl4ai-mcp/scale {"replicas":20}`.
2. Gateway writes `desired_replicas=20`, sets `routing_mode=pooled`, calls `reconcile_server`.
3. Reconcile starts containers `crawl4ai-mcp` (index 1, existing) + `crawl4ai-mcp-2 … crawl4ai-mcp-20`, all image `hackerdogs/crawl4ai-mcp:latest`, all on `mcpfarm_internal`, all internal port `8521`, env `CRAWL4AI_URL`/`CRAWL4AI_API_TOKEN` injected.
4. Per-instance health probes flip `health_ok` true as each becomes ready; aggregate `crawl4ai-mcp.health_ok=true` after the first.
5. Caddy exposes one route `/crawl4ai-mcp/*` → `reverse_proxy auth-gateway:9090` (pooled), and the gateway sticky-routes across the 20 healthy replicas.
6. A client `initialize` → gateway picks the least-loaded replica, records `session_affinity`; all subsequent same-session calls pin to that replica.
7. Scaling back: `{"replicas":3}` → reconcile stops indices 4–20, prunes their instance rows and any affinity entries, reloads Caddy once.
