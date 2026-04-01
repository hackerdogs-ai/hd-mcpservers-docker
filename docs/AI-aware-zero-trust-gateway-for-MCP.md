# AI-aware zero-trust gateway for MCP

**Status:** Canonical architecture and product specification  
**Scope:** Hackerdogs MCP server farm and the security gateway that fronts it

This document is the **single source of truth** for what we build: an **AI-aware zero-trust gateway** that sits in front of a large catalog of MCP security-tool servers, enforcing identity, policy, and safety **before** tools execute—while remaining **transparent** to standard MCP clients (URL + headers, streamable HTTP).

---

## Architecture overview

This section names **third-party open source** building blocks (not Hackerdogs-authored services such as `auth-gateway` or MCP server images), where each sits in **data flow**, and how that compares to the diagrams in [`FARM-PRD.md`](./FARM-PRD.md) and [`ChatGPT Guidance on MCP Server Farm.md`](./ChatGPT%20Guidance%20on%20MCP%20Server%20Farm.md). **§3** below shows the same stack as **logical layers (L0–L5)**.

### Third-party open source components

| Component | Typical license | Purpose | Position in data flow |
|-----------|-----------------|---------|------------------------|
| **cloudflared** | Apache 2.0 | Outbound-only tunnel from host to Cloudflare; public TLS at edge; no inbound firewall holes. | **L0** — First hop inside the farm after Cloudflare Edge; forwards HTTP to Caddy. |
| **Caddy** | Apache 2.0 | Reverse proxy, path routing, `forward_auth` to validate Bearer tokens before upstream. | **L1** — Terminates farm HTTP from tunnel; routes `/{server}/…`; calls auth; proxies to L3 or L4. |
| **PostgreSQL** | PostgreSQL License | Durable OLTP: API keys (hashed), server registry, relational constraints. | **L2 side path** — Read/written by **auth-gateway** on every `/verify` and admin API call; not on the hot proxy path as raw SQL inside Caddy. |
| **TimescaleDB** | Timescale License (Apache 2.0 core) | Time-series extension on PostgreSQL: **hypertables** for high-volume `request_log` / `policy_event_log`, retention & compression. | **L2 side path** — Same DB process as Postgres; append-heavy audit and analytics queries. |
| **Redis** | BSD 3-Clause | Shared sliding-window rate limits when **multiple** auth-gateway replicas run. | **L2 side path** — Optional at single-node; recommended before scaling gateways horizontally. |
| **Docker Engine** + **Docker Compose** | Apache 2.0 | Container runtime and multi-service orchestration for the farm. | **Platform** — Hosts all containers on `mcpfarm_internal` (or equivalent bridge). |

**L3 — pick one MCP-native proxy (tool-call firewall):**

| Component | Typical license | Purpose | Position in data flow |
|-----------|-----------------|---------|------------------------|
| **PolicyLayer Intercept** | Apache 2.0 | YAML policies; MCP `tools/list` / `tools/call` interception; sub-ms deterministic decisions. | **L3** — Between Caddy (post-auth) and MCP server; inspects JSON-RPC before tools run. |
| **mcpwall** (behrensd) | Apache 2.0 | Lightweight “iptables for MCP”; YAML; audit logging. | **L3** — Same logical slot as PolicyLayer. |
| **IronCurtain** | Apache 2.0 | Constitution-style rules compiled to checks; MCP proxy. | **L3** — Same slot. |
| **AvaKill** | AGPL-3.0 | Rich rule set + MCP proxy mode; OS sandbox hooks. | **L3** — Same slot; license stricter for distribution. |
| **ressl/mcp-firewall** | AGPL-3.0 | Enterprise-style checks + OPA/Rego; signed audit trails. | **L3** — Same slot; heavier compliance focus. |

**Phased security / ingress hardening (P2–P4)** — optional extensions to the GA path; see **§9** for objectives and how they differ from observability (§8):

| Component | Typical license | Purpose | Position in data flow |
|-----------|-----------------|---------|------------------------|
| **Envoy Proxy** / **Envoy Gateway** / **Envoy AI Gateway** | Apache 2.0 | Advanced ingress: MCP-aware routing, JWT/OAuth, multiplexing, filters. | **L1** (or in front of Caddy) — **P2** substitute or complement to Caddy-only ingress. |
| **Open Policy Agent (OPA)** | Apache 2.0 | Rego policy decisions; often paired with Envoy `ext_authz`. | **L2/L3 decision** — External authorization; may complement or replace YAML-only L3. |
| **Coraza** (WAF, e.g. proxy-wasm) | Apache 2.0 | OWASP-style HTTP/WAF checks, body limits, CRS-style rules. | **L1 / L3 edge** — **P2/P3** protocol hardening. |
| **Microsoft Presidio** | MIT | PII detection / redaction in text. | **P3** — Request/response **data-protection** path (security control; not “monitoring”). |
| **TruffleHog** | AGPL-3.0 | Secret detection in payloads. | **P3** — Same **data-loss prevention** class as Presidio. |
| **KubeArmor** | Apache 2.0 | eBPF/LSM runtime enforcement (Kubernetes/Linux). | **L5** — **P4** preventive enforcement on workloads. |
| **Falco** | Apache 2.0 | Runtime threat detection (syscalls, K8s audit). | **L5** — **P4** detective control at runtime. |

**Observability plane (§8)** — orthogonal to preventive MCP security; ships on its own timeline:

| Component | Typical license | Purpose | Position |
|-----------|-----------------|---------|----------|
| **OpenTelemetry Collector** | Apache 2.0 | Traces, metrics, logs pipeline (OTLP). | Sidecar / daemon — **not** on the authorization path. |
| **Jaeger** | Apache 2.0 | Distributed trace backend. | Telemetry store. |
| **Grafana** | AGPL-3.0 | Dashboards, alerting on metrics/logs. | Operations UI. |
| **ClickHouse** | Apache 2.0 | Columnar store for very high-volume log analytics. | Optional complement to **TimescaleDB hypertables** (§7) for OLAP-style exploration. |

**Companion plane (outside MCP farm HTTP path)** — optional; addresses prompt-layer abuse the MCP path may not see:

| Component | Typical license | Purpose | Position in data flow |
|-----------|-----------------|---------|------------------------|
| **InferShield** | MIT | Reverse proxy: LLM API input/output scanning (injection, encoding tricks). | **Between agent app and LLM provider** — Before the model plans tool calls. |
| **LlamaFirewall** (Purple Llama) | Custom / MIT (components) | ML/heuristic scanners for jailbreak, alignment, code safety. | **Agent or LLM egress** — Pre–tool-call pipeline. |
| **NeMo Guardrails** | Apache 2.0 | Colang DSL flows; conversational and tool-adjacent rails. | **Agent orchestration layer** — LangChain/LlamaIndex integration. |

*Licenses are typical; verify current SPDX for your version before redistribution.*

### Data flow diagram (MCP request path — GA target)

Aligned with [FARM-PRD §3](./FARM-PRD.md#3-architecture) and §3.1 **request flow**, with **L3**, **PostgreSQL + TimescaleDB**, and optional **Redis**. **Caddy** issues a **`forward_auth` subrequest** to **auth-gateway** first; only on **2xx** does the **main** request continue to L3 (or straight to MCP if L3 is not deployed).

```
                         Internet (TLS)
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Cloudflare Edge    │
                    └──────────┬───────────┘
                               │  tunnel (outbound)
                               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                     DOCKER BRIDGE (e.g. mcpfarm_internal)                   │
│                                                                               │
│  ┌─────────────┐         ┌─────────────────────────────────────────────┐   │
│  │ cloudflared │────────▶│  Caddy :80                                   │   │
│  └─────────────┘         │       │                                      │   │
│                          │       │ ① subrequest: forward_auth /verify   │   │
│                          │       ▼                                      │   │
│                          │  ┌──────────────────┐    ┌───────────────┐ │   │
│                          │  │  auth-gateway    │───▶│ PostgreSQL    │ │   │
│                          │  │  :9090           │    │ + TimescaleDB │ │   │
│                          │  │  (Bearer, scopes,│    │ (OLTP +       │ │   │
│                          │  │   rate limit)    │    │  hypertables) │ │   │
│                          │  └────────┬─────────┘    └───────┬───────┘ │   │
│                          │           │                      │        │   │
│                          │           └──────────┬─────────────┘        │   │
│                          │                      │                      │   │
│                          │                      ▼                      │   │
│                          │               ┌─────────┐ (optional)       │   │
│                          │               │  Redis  │ multi-replica    │   │
│                          │               └─────────┘ rate windows     │   │
│                          │                                             │   │
│                          │ ② main request (after auth 2xx)             │   │
│                          └──────┬──────────────────────────────────────┘   │
│                                 │                                             │
│                                 ▼                                             │
│                    ┌────────────────────────────┐                            │
│                    │  L3 MCP policy proxy         │  (PolicyLayer / mcpwall /  │
│                    │  tools/call inspection       │   …) — GA mandatory        │
│                    └─────────────┬──────────────┘                            │
│                                  │ HTTP reverse_proxy                        │
│                                  ▼                                            │
│                    ┌─────────┐ ┌─────────┐ ┌─────────┐   … 155+ MCP containers │
│                    │ naabu-  │ │ trivy-  │ │  …      │   (FastMCP streamable)  │
│                    │ mcp     │ │ mcp     │ │         │                         │
│                    └─────────┘ └─────────┘ └─────────┘                         │
└──────────────────────────────────────────────────────────────────────────────┘
```

*Note:* **Pre-GA / dev only:** omit the L3 box; Caddy **`reverse_proxy`** goes **directly** to the target MCP service after `forward_auth`. **Admin API** traffic (`/admin/*`) is proxied by Caddy to auth-gateway on the **main** path (not shown in every step).

*L3 internal validate:* Some designs have L3 call **`auth-gateway` internal validate** again to load `key_id`/scopes; that is an extra hop on the **main** request path—see §12.2.B.

### Extended reference diagram (optional P2–P4 security stack + §8 telemetry)

Condensed from extended architecture guidance: **P2–P4** adds ingress/policy/DLP/runtime controls; **telemetry** (OTel → Jaeger/Grafana/ClickHouse) runs **out of band** for SRE and does not replace L2/L3 enforcement—see **§8**.

```
  MCP clients / agents
           │
           ▼
  ┌────────────────┐      ┌─────────────┐      ┌──────────────────┐
  │ Envoy (AI GW)  │─────▶│ OPA / Coraza │─────▶│  Caddy + L3 +   │──▶ MCP farm
  │  [optional P2] │      │  [optional]  │      │  auth-gateway   │
  └────────────────┘      └─────────────┘      └────────┬─────────┘
                                                        │
                        ┌───────────────────────────────┼────────────────┐
                        ▼                               ▼                ▼
                 ┌────────────┐                  ┌────────────┐   ┌──────────┐
                 │ Presidio / │                  │ OTel       │──▶│ Jaeger / │
                 │ TruffleHog │                  │ Collector  │   │ Grafana /│
                 │ [P3]       │                  │            │   │ ClickHouse│
                 └────────────┘                  └────────────┘   └──────────┘

  Host / K8s:  KubeArmor + Falco [P4] — runtime around MCP workloads
```

### Companion plane (LLM path — not the MCP URL)

```
  Agent application
        │
        ├──────────────────────────▶ LLM provider API
        │                                    ▲
        │   ┌────────────────────────────────┘
        │   │  InferShield / LlamaFirewall / NeMo [optional]
        │
        └──────────────────────────▶ https://farm/{server}/mcp/  (MCP path above)
```

---

## 1. Thesis

**Zero-trust:** No request is trusted based on network position alone. Every tool invocation is authenticated, authorized, and evaluated against policy with explicit allow/deny/redact/approve outcomes.

**AI-aware:** The gateway assumes tool calls may originate from **compromised, confused, or manipulated models and agents** (prompt injection, indirect injection via retrieved content, scope abuse, SSRF-shaped arguments, exfiltration). Policy is **tool- and argument-aware**, not only URL- or API-key-aware.

**MCP-native:** Enforcement understands MCP over HTTP (e.g. JSON-RPC methods, `tools/call`, tool names, structured arguments, and responses where inspected)—not generic HTTP reverse-proxy rules alone.

---

## 2. Goals

| Goal | Description |
|------|-------------|
| **Single gateway story** | One named architecture: layers, phases, and responsibilities—no parallel “farm doc” vs “firewall doc” as competing specs. |
| **Transparent to clients** | Users point MCP clients at `https://…/{server}/mcp/` with Bearer token (and optional upstream `X-*` headers); protocol and errors stay standard MCP. |
| **Operator-owned safety** | Policies and guardrails are **infrastructure**, controlled by the farm operator—not opt-in per end user. |
| **Scalable catalog** | Many independent MCP server containers (155+), uniform URL scheme, dynamic registration where required. |
| **Phased depth** | Ship a minimal viable gateway quickly; add inspection, advanced ingress, and runtime hardening in defined phases without redesign. |

Non-goals for v1 of the gateway are listed per phase (see §9).

---

## 3. Logical architecture (layers)

Traffic flows **through** these layers in order. Implementation may map multiple layers onto one process in early phases; the **roles** stay stable. **Third-party products** mapped to each layer and **ASCII data-flow** diagrams are in **Architecture overview** at the top of this document.

```
Clients / LLM agents
        │
        ▼
┌───────────────────────────────────────────────────────────┐
│ L0  Edge connectivity                                     │
│     e.g. Cloudflare Tunnel — TLS to edge, no inbound      │
│     ports on host                                         │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│ L1  Ingress & transport                                   │
│     HTTP termination (where applicable), routing, stream   │
│     handling; may include global rate limits              │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│ L2  Authentication & tenancy                              │
│     Verify Bearer API keys; scopes per MCP server;        │
│     per-key rate limits; audit events; optional future    │
│     tenant / org claims                                   │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│ L3  AI-aware MCP policy plane (mandatory at GA)           │
│     MCP-native intercept: tool allowlists, argument       │
│     rules, SSRF/metadata patterns, trust-tier defaults,   │
│     deterministic “hot path” decisions                    │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│ L4  MCP server farm                                       │
│     Reverse proxy to correct container; health; dynamic   │
│     registration; Hackerdogs FastMCP `/mcp/` contract     │
└───────────────────────────┬───────────────────────────────┘
                            ▼
┌───────────────────────────────────────────────────────────┐
│ L5  Workload isolation                                    │
│     Container constraints; optional host/runtime          │
│     telemetry and enforcement on supported platforms      │
└───────────────────────────────────────────────────────────┘
```

**Companion plane (optional, not always in farm compose):**  
**LLM egress / agent-side guard** — inspects prompts and model I/O **before** tool calls are formed. The MCP gateway **does not** guarantee visibility of the full chat transcript unless the client or agent forwards it or embeds it in tool arguments. Serious deployments treat **MCP policy (L3)** and **LLM/agent guards** as **complementary**, both described here as one security model.

---

## 4. Policy model (AI-aware, tool-centric)

For every evaluated request, the gateway (L3 + L2 context) should be able to decide, at minimum:

- **ALLOW** — forward to the MCP server.  
- **ALLOW_WITH_REDACTION** — response or request fields stripped per policy (when inspection exists).  
- **REQUIRE_APPROVAL** — block until human or break-glass workflow (when implemented).  
- **DENY** — standard MCP error to client; no bespoke firewall protocol required.  
- **QUARANTINE_SESSION / KEY** — operator policy for repeated abuse (when implemented).

**Inputs to policy** (extend over time):

- Key identity, scopes, rate-limit state.  
- MCP method, server route, **tool name**, structured **arguments** (URLs, hosts, paths, commands, queries).  
- Optional **security metadata envelope** (agent id, session id, model id, approval state)—recommended for enterprise deployments.  
- Trust **tier** of the target MCP server (see §5).

**Hot path rule:** Default decisions in L3 must stay **deterministic and low-latency** (e.g. YAML/Rego/regex, allowlists). Heavier ML or async analytics are **warm/cold** paths only.

---

## 5. Trust tiers for MCP servers

Servers are classified so default policies can differ without per-tool bespoke work for every binary.

| Tier | Examples (illustrative) | Default posture |
|------|-------------------------|-----------------|
| **T0** | Public read / low sensitivity | Broader tool allow, standard injection-style argument checks |
| **T1** | Authenticated read (repos, tickets) | Scoped keys, destination restrictions, audit |
| **T2** | Sensitive internal data | Stricter args, output handling, short-lived context |
| **T3** | Write / exec / send / cloud admin | Default deny for risky patterns; approval gates |

---

## 6. Product contract (client-visible)

- **Base URL:** `https://<farm-host>/{server-name}/mcp/` (streamable HTTP as exposed by FastMCP).  
- **Authentication:** `Authorization: Bearer <farm_api_key>`.  
- **Upstream tool keys:** Passed as `X-*` headers; **not** stored in the farm DB; per-request isolation in server middleware.  
- **Transparency:** Gateway and policies are invisible in the happy path; denials look like normal MCP failures unless the product chooses to expose reason codes later.

Detailed admin API, compose layout, port maps, and migration constraints (e.g. no Minibridge in farm images) remain **implementation specifics** documented alongside this spec in the repository.

---

## 7. Persistence & tenant data plane

This section covers **durable data** the product owns: tenants, keys, catalog, and **append-only audit/evidence** suitable for compliance and incident review. It is **not** the telemetry/observability architecture—that is **§8**.

### 7.1 Canonical store: PostgreSQL + TimescaleDB

**Product default:** The auth-gateway uses **PostgreSQL** with the **TimescaleDB** extension—not SQLite—so **multi-tenant OLTP**, **concurrent gateway replicas**, and **high-volume audit inserts** do not force a disruptive migration later.

| Store | Role |
|-------|------|
| **PostgreSQL** (relational tables) | **`tenants`**, **`platform_mcp_servers`**, **`api_keys`**, **`api_key_mcp_grants`**, optional **`tenant_mcp_deployments`** — transactional source of truth; **`/verify`** resolves **`key_hash`** then enforces tenant status, **`scope_mode`**, and grants. Primary keys: **ULID `TEXT`** (application-generated). |
| **TimescaleDB hypertables** | **Time-partitioned audit/evidence**: **`request_log`** (L2 access record per call), **`policy_event_log`** (L3 decision record). Optimized for **retention**, **compression**, and **time-range queries** (e.g. “all denials for tenant X in the last 7 days”). |

**Schema:** [`docs/schema/mcp-farm-timescaledb.sql`](./schema/mcp-farm-timescaledb.sql) — multi-tenant FKs, optional commented RLS for analyst-only roles, Timescale **compression** segmenting by **`tenant_id`** + **`server_key`**.

**Runtime:** e.g. `timescale/timescaledb-ha:pg16` or `timescale/timescaledb:latest-pg16`; apply schema via migrations on deploy. Overlap with [FARM-PRD §4.2](./FARM-PRD.md#42-auth-gateway-api-only) is **conceptual** only—this file and the SQL schema supersede PRD table names.

### 7.2 Audit record model (what the database must capture)

These rows are **evidence**, not live metrics streams. Minimum conceptual fields:

| Stream | Table (hypertable) | Purpose |
|--------|-------------------|---------|
| **L2 access** | `request_log` | Who (key/tenant), which `server_key`, HTTP status/latency, optional `client_request_id` for correlation with **§8** traces. |
| **L3 policy** | `policy_event_log` | `policy_action`, `policy_reason_code`, `tool_name`, `args_sha256`, latency—supports investigations and compliance reporting. |

Do **not** store full tool arguments or upstream secrets unless a written data-retention policy requires it; prefer **hashes** and **reason codes**.

### 7.3 Redis (coordination only)

**Redis** is **not** the system of record. Use it for **ephemeral** sliding-window **rate-limit counters** when multiple auth-gateway processes share load. Authoritative keys and audit history remain in **§7.1**.

---

## 8. Observability, telemetry, and analytics

Observability answers: *Is the platform healthy? Where is latency? What failed after deployment?* **Product security** (L2/L3/L5) answers: *Should this request run at all?* The two intersect for **detection and response**, but they are **different workstreams** and **different budgets**.

### 8.1 Separation of concerns

| Concern | Primary owner in this architecture | Typical consumers |
|---------|-----------------------------------|-------------------|
| **Preventive access control** | L2 auth-gateway, L3 MCP policy proxy | Product security, tenant isolation |
| **Durable audit / evidence** | §7 hypertables (`request_log`, `policy_event_log`) | Security operations, compliance, forensics |
| **Telemetry (metrics, traces, logs)** | OpenTelemetry Collector + backends (§8.3) | SRE, on-call, capacity planning |
| **Analytics & BI** | SQL against Timescale, Grafana/ClickHouse dashboards | Product, finance (usage), security analytics |

**Anti-pattern:** Treating Grafana or Jaeger as “security” because traces exist. They **do not enforce** policy; they **observe** behavior after instrumentation. **P3** components such as Presidio/TruffleHog **are** security controls (data loss / secret exposure prevention) and belong in the **request/DLP path**—see **§9.5**.

### 8.2 Telemetry stack (recommended shape)

1. **Instrumentation:** OTel SDKs or auto-instrumentation in **auth-gateway**, **L3 proxy**, and optionally **Caddy** (where supported). Standard resource attributes: `service.name`, `deployment.environment`, `tenant_id` (if safe to export—often hashed or omitted for privacy).
2. **Pipeline:** **OpenTelemetry Collector** — receive OTLP, batch, filter PII from log bodies, export to backends.
3. **Backends:** **Prometheus-compatible metrics** (or Grafana Mimir), **Jaeger** or Grafana Tempo for traces, **Loki** or centralized logging for unstructured logs.
4. **Correlation:** Propagate **`client_request_id`** / trace id into **§7** audit rows where possible so an alert in Grafana can pivot to a specific `policy_event_log` row.

Sampling, cardinality limits, and **redaction** of `Authorization` and `X-*` headers in log exporters are **mandatory** operational requirements.

### 8.3 Product analytics vs security audit

**TimescaleDB** hypertables serve **both** (a) **security audit** time series and (b) **product analytics** (e.g. QPS per tenant, top tools). Distinguish them in **access control**: reporting roles may get `SELECT` on aggregates; only security roles get raw `policy_reason_code` lines if policy demands it. Optional **ClickHouse** (or a warehouse) is for **federated** or **petabyte-scale** exploration—not a replacement for §7 OLTP.

### 8.4 Security monitoring (detective layer)

Runbooks should define: **alerts** on error rate spikes, L3 deny-rate anomalies, auth **401/403** bursts, and DB replication lag. These use **telemetry + §7 SQL** together: metrics trigger investigation; hypertables provide **ground truth** for “who did what.” **P4** tools (**Falco**, etc.) add **runtime** signals—still **detective**, not a substitute for L3.

---

## 9. Roadmap: delivery phases (P0–P4)

Phases are **delivery ordering**, not a claim that “P4 = security.” **Security GA** is **P0 + P1**. **P2–P4** add **defense-in-depth**, **ingress scale**, **DLP-style inspection**, and **runtime controls**. **§8 observability** should begin **during P0** (minimal health/metrics) and deepen in parallel—it is **not** gated on P4.

### 9.1 Phase summary

| Phase | Name | Security objective | Platform / ops objective |
|-------|------|--------------------|---------------------------|
| **P0** | Foundation | Authenticate every MCP request; **tenant-scoped** keys and grants; **no** direct exposure of MCP containers; durable **§7** audit of access. | Single `docker compose` (or equivalent); tunnel + Caddy + auth-gateway + Postgres/Timescale; admin API; catalog wiring. |
| **P1** | MCP policy GA | **Mandatory L3:** tool- and argument-aware **deny/allow** before tools execute; trust-tier defaults; policy events in **`policy_event_log`**. | Latency budget for L3 hot path; negative tests; operator policy lifecycle. |
| **P2** | Advanced ingress & policy engine | Stronger **identity at the edge** (OAuth/JWKS, mTLS if required); optional **OPA** for complex Rego; **Coraza**/WASM for protocol abuse. | Replace or augment Caddy when MCP multiplexing or fleet-wide filter rollout demands it; version-pinned gateways. |
| **P3** | Content & data protection | **Presidio** / **TruffleHog** (or equivalents) on request/response paths; **redaction** and secret blocking—**security controls**, with latency/async design. | Bounded buffers, sampling, false-positive tuning; **not** the same team milestone as “turn on Grafana.” |
| **P4** | Runtime hardening | **KubeArmor** / **seccomp** / **network egress allowlists** reduce blast radius if a container is compromised. | Linux-first ops; Kubernetes or hardened Docker hosts; **Falco**-class alerts feed **§8.4**. |

### 9.2 P0 — Foundation (detail)

**Entry:** Empty environment. **Exit:** End-to-end MCP call with Bearer auth; rows in `request_log`; tenant and keys manageable via admin API; §8.2 minimal health endpoint and container logs sufficient for first on-call.

### 9.3 P1 — MCP policy GA (detail)

**Entry:** P0 stable. **Exit:** Every production MCP route passes L3; integration tests for SSRF-shaped args and disallowed tools; `policy_event_log` populated; documented **rollback** (disable L3 route) for emergencies.

### 9.4 P2 — Advanced ingress (detail)

**Entry:** P1 stable; documented pain (auth at edge, rule complexity, or scale). **Exit:** ADR recorded; ingress chart/version pinned; no double-auth loops; OPA/Envoy **only** if operators can own CRD/schema upgrades.

### 9.5 P3 — Content inspection (detail)

**Entry:** P1 stable; DLP or compliance driver. **Exit:** Written policy for **ALLOW_WITH_REDACTION**; max buffer sizes; PII/secrets test corpus; latency SLO for inspected vs bypass traffic.

### 9.6 P4 — Runtime hardening (detail)

**Entry:** Production on Linux (or K8s). **Exit:** Profiles validated per MCP image; egress policy documented; Falco/KubeArmor rules reviewed for noise.

### 9.7 General availability bar

**GA (security):** **P0 + P1** complete. **LLM/agent-side guards** (companion plane) **recommended** for high-risk cyber-tool exposure but are **outside** this farm’s HTTP path.

**Observability maturity:** By GA, **§8.2** should provide **metrics + traces** for auth-gateway and L3 at minimum; full Grafana/ClickHouse is **operational maturity**, not a GA security gate.

---

## 10. Security controls & residual risk

This section summarizes **control types**; detailed implementation remains in **§3–§7**, **§9**, and [`FARM-PRD.md`](./FARM-PRD.md).

| Control class | Examples in this architecture | Residual risk if misconfigured |
|---------------|------------------------------|--------------------------------|
| **Preventive (network)** | Cloudflare Tunnel, internal bridge only, no host-published MCP ports | Misrouted tunnel origin exposes Caddy without intended edge policies |
| **Preventive (identity)** | Bearer keys, tenant status, `scope_mode`, `api_key_mcp_grants` | Weak admin secret; key material logged |
| **Preventive (MCP)** | L3 tool/argument policy | Bypass if L3 omitted or Caddy routes skip L3 |
| **Detective (data)** | §7 hypertables, §8.4 alerts | Retention too short for investigations |
| **Detective (runtime)** | Falco, K8s audit (P4) | Alert fatigue; missed signals |
| **Corrective** | Key revocation, tenant `suspended`, emergency L3 bypass procedure | Depends on runbooks and staffing |

**Operational notes:** **Docker socket** on auth-gateway is high-value—minimize privileges and audit `/admin/servers`. **Public `/services`** is a recon tradeoff—document the decision. **License** posture (Apache vs AGPL) for L3 and P3 scanners must match your **distribution** model.

---

## 11. Relationship to other documents

- **`docs/FARM-PRD.md`** — Compose detail, admin API tables, dynamic registration, guardrail catalog. **Persistence:** PRD may still mention SQLite for minimal dev; **canonical store is §7** and [`docs/schema/mcp-farm-timescaledb.sql`](./schema/mcp-farm-timescaledb.sql). This spec wins on conflict.  
- **`docs/ChatGPT Guidance on MCP Server Farm.md`** — Reference ideas for **P2–P4** and telemetry backends; map components to **§8** (observability) vs **§9** (phased security)—not a parallel spec.

---

## 12. Step-by-step implementation guide (zero to hero)

This section is the **execution path** from nothing running to a **production-shaped** AI-aware zero-trust MCP gateway. It maps to **§9 phases** (P0–P4), adds a **parallel observability track** (**§12.6**, aligned with **§8**), and includes **technical contracts** (HTTP, Caddy `forward_auth`, auth-gateway behavior, MCP JSON-RPC, Compose networking). **§12.0A** is the **index of every third-party OSS component** from **Architecture overview** → **subsection + step**. Full SQL and admin API tables remain in [`FARM-PRD.md`](./FARM-PRD.md).

**Legend:** Steps marked **(build)** are required when the `mcpfarm/` stack (or equivalent) is not yet in the repository.

**Outline:** **12.0** Prerequisites + **§12.0A OSS master map** → **12.1** P0 + **§12.1.A–I** → **12.2** P1 + **§12.2.A–F** → **12.3–12.5** P2–P4 → **12.6** Observability (§8 parallel) → **12.7** Companion plane → **12.8** Scaling → **12.9** Troubleshooting → **12.10** Final checklist.

---

### 12.0 Prerequisites (before P0)

| Step | Action | Done when |
|------|--------|-----------|
| 0.1 | Install **Docker Engine** (24+) and **Docker Compose v2**. | `docker compose version` works. |
| 0.2 | Install **Python 3.11+** for compose/route generators. | `python3 --version` ≥ 3.11. |
| 0.3 | Read **§3 (layers)** and **§9 (phases)** in this document. | You can explain L0–L5 in one sentence each. |
| 0.4 | Choose **edge**: Cloudflare Tunnel (recommended for no open inbound ports) **or** TLS on your own load balancer later. | You know your public hostname (e.g. `mcp.example.com`). |
| 0.5 | Generate secrets: long random `ADMIN_SECRET`; plan **SHA-256** storage for API keys (never store plaintext). | Secrets in a password manager, not in git. |

**Technical — reproducibility:** In runbooks or CI, **pin** Docker Engine / Compose plugin versions and record **image digests** after `docker compose pull` (`docker image inspect …`) so you can bisect regressions.

### 12.0A Open source components → where they appear in §12

Every third-party product listed in **Architecture overview** (top of this document) should be **introduced on purpose** in a numbered step—not only mentioned in prose. Use this table as the implementation index; **§9** defines *when* a phase is in scope for GA vs optional.

| Open-source component | Layer / plane | §9 phase | §12 section | Step(s) / subsection |
|------------------------|---------------|----------|-------------|----------------------|
| **Docker Engine** | Platform | P0 | **12.0** | 0.1 |
| **Docker Compose** | Platform | P0 | **12.0**, **12.1** | 0.1, 1.3, 1.9; **§12.1.I** |
| **cloudflared** | L0 | P0 | **12.1** | 1.7; **§12.1.F** |
| **Caddy** | L1 | P0 | **12.1** | 1.6, 1.14; **§12.1.D** |
| **PostgreSQL** | L2 data | P0 | **12.1** | 1.4; **§12.1.C** |
| **TimescaleDB** (extension) | L2 audit hypertables | P0 | **12.1** | 1.4; **§12.1.C**; tune in **12.8** (step 8.4) |
| **Redis** | L2 coordination | P0 optional → **required** before multi-replica gateway | **12.8** | 8.2 |
| **Hackerdogs `*-mcp` images** (FastMCP) | L4 | P0 | **12.1** | 1.2, 1.3, 1.11; **§12.1.B–E** |
| **PolicyLayer Intercept** / **mcpwall** / **IronCurtain** / **AvaKill** / **ressl/mcp-firewall** (pick one) | L3 | P1 (GA) | **12.2** | 2.1–2.8; **§12.2.A–F** |
| **Envoy Proxy** / **Envoy Gateway** / **Envoy AI Gateway** | L1 (alt.) | P2 | **12.3** | 3.1 |
| **Open Policy Agent (OPA)** | L2/L3 policy | P2 | **12.3** | 3.2 |
| **Coraza** (WAF / proxy-wasm) | L1/L3 edge | P2 / P3 | **12.3**, **12.4** | 3.x (ingress); **4.2** (body limits / WAF) |
| **Microsoft Presidio** | P3 DLP | P3 | **12.4** | 4.1 |
| **TruffleHog** | P3 secrets | P3 | **12.4** | 4.1 |
| **OpenTelemetry Collector** | §8 telemetry | Parallel **with P0+** | **12.6** | 6.1 |
| **Jaeger** (or Grafana Tempo) | §8 traces | Parallel | **12.6** | 6.3 |
| **Grafana** (+ Mimir/Loki as chosen) | §8 UI / metrics / logs | Parallel | **12.6** | 6.3 |
| **ClickHouse** | §8 optional analytics | Parallel / scale | **12.6** | 6.4 |
| **KubeArmor** | L5 enforcement | P4 (K8s/Linux) | **12.5** | 5.4 |
| **Falco** | L5 detection | P4 | **12.5** | 5.3 |
| **InferShield** / **LlamaFirewall** / **NeMo Guardrails** | Companion (LLM path) | Recommended high-risk | **12.7** | 7.1–7.2 |

*Custom code (**auth-gateway**, generators) is not in this table; it is built in **12.1** steps 1.4–1.5.*

---

### 12.1 P0 — Foundation (layers L0, L1, L2, L4)

**Outcome:** Tunnel (or edge) → ingress → **authenticated** proxy → MCP containers; **admin API** for keys and registry; **no L3 yet** is acceptable only for internal dev—**treat P0+P1 as GA** per §9.

**Open source in this section:** **Docker** / **Compose**, **cloudflared**, **Caddy**, **PostgreSQL** + **TimescaleDB**, **Hackerdogs MCP images**; **Redis** only after you plan multiple gateway replicas (**§12.8**). Cross-check every row in **§12.0A** whose phase is **P0**.

**Why a dedicated farm directory (e.g. `mcpfarm/`) if MCP servers already live in this repo?**  
The existing folders (e.g. `naabu-mcp-server-mcp/`, `trivy-mcp-server-mcp/`, …) are **per-server packages**: Dockerfiles, Python MCP code, `test.sh`, tool-specific deps. They do **not** include the **shared control plane** for running **many** servers as one product: **Caddy** (routing + `forward_auth`), **auth-gateway** (keys, scopes, audit, optional Docker API), **tunnel** wiring, **`port-map.json` + generator** (one compose graph and `routes.conf` for 155+ services), and **`.env`** for farm-wide secrets. That orchestration is a **different artifact** from any single MCP server. Putting it under one directory (the PRD names it `mcpfarm/`) keeps **ingress/auth/compose generation** in one place, avoids sprinkling gateway code into 155 server trees, and lets compose **reference published images** (`hackerdogs/*-mcp:latest`) built from those server folders—without nesting 155 `build:` contexts in one mega-folder. **`mcpfarm/` is a convention, not a law:** the same layout could live at repo root or under `deploy/mcp-farm/` as long as those components exist somewhere discoverable.

| Step | Action | Done when |
|------|--------|-----------|
| 1.1 **(build)** | Create the **farm orchestration** layout (PRD name: `mcpfarm/`—or an equivalent path) per [FARM-PRD §8.1](./FARM-PRD.md#81-directory-structure): `caddy/`, `auth-gateway/`, `cloudflared/` (or tunnel env only), `scripts/`, `port-map.json`. Do **not** duplicate each MCP server’s source here; only infra + generators + gateway code. | Directories and placeholders exist. |
| 1.2 **(build)** | Author **`port-map.json`**: map each MCP server name → internal port (see [FARM-PRD §7](./FARM-PRD.md#7-port-allocation-strategy)). Start with a **small subset** (2–5 servers) for faster iteration. | Generator can read the file. |
| 1.3 **(build)** | Implement **`scripts/generate-compose.py`**: emit `docker-compose.yml` service blocks for infra + each MCP image (`hackerdogs/<name>-mcp:latest`), internal network only, **no** `ports:` on MCP services. | `docker compose config` validates. |
| 1.4 **(build)** | Implement **auth-gateway** (FastAPI): `GET /verify` for Caddy `forward_auth`; **PostgreSQL** for `api_keys` and `servers`; **hypertables** for `request_log` (and `policy_event_log` when L3 exists) per [`docs/schema/mcp-farm-timescaledb.sql`](./schema/mcp-farm-timescaledb.sql); hash keys at rest; connection pool + migrations. | Local hit to `/verify` returns 200/401; DB schema applied. |
| 1.5 **(build)** | Implement admin API: `POST/GET/PATCH/DELETE /admin/keys`, server registry, audit query paths, `X-Admin-Secret` on admin routes. | You can create a key via `curl` (see PRD §4.3). |
| 1.6 **(build)** | **Caddyfile**: health, `/admin/*` and `/services` to auth-gateway, `import` of generated **`routes.conf`**; each route: `forward_auth` → strip prefix → `reverse_proxy` to container. | One MCP server reachable internally through Caddy. |
| 1.7 | Add **`cloudflared`** service with `TUNNEL_TOKEN` **or** document alternate edge; tunnel targets **Caddy:80** on the internal network. | Public URL loads `/health` (or equivalent). |
| 1.8 | Create **`.env`** from `.env.example`: `TUNNEL_TOKEN`, `ADMIN_SECRET`, optional upstream keys for shared defaults. | No secrets committed. |
| 1.9 | Run **`python scripts/generate-compose.py`**, then **`docker compose pull && docker compose up -d`**. | All targeted containers healthy. |
| 1.10 | **Bootstrap keys:** seed tenant + `POST /admin/keys` (or equivalent); keys use **`scope_mode`** + **`api_key_mcp_grants`** per **§7** schema (not a CSV `scopes` string). | User key cannot call disallowed `server_key` (403). |
| 1.11 | **Verify MCP:** `POST` a valid MCP/JSON-RPC message to `https://<host>/<server>/mcp/` with `Authorization: Bearer …` (use client or `curl`). | Tool list or session initializes without 401. |
| 1.12 | **Configure a real MCP client** (Cursor, Claude, etc.) with `streamable-http` URL and headers per [FARM-PRD §8.4](./FARM-PRD.md#84-client-configuration). | End-to-end tool call succeeds. |
| 1.13 **(optional)** | Implement **dynamic server registration** (Docker socket on gateway, Caddy reload)—per PRD §5. | New server appears at new path without full stack restart. |
| 1.14 | **Hardening pass:** ensure Caddy/access logs **redact** `Authorization` and sensitive `X-*` headers; confirm MCP containers are **not** published to host ports. | Log sample shows no raw secrets. |

#### 12.1.A Docker network and ports

- Attach **all** farm services to one user-defined bridge (e.g. `mcpfarm_internal`). Compose **service names** are stable **DNS names** on that network (`caddy`, `auth-gateway`, `naabu-mcp`, …).
- **Do not** map MCP service ports to the host. Ingress should be **cloudflared → caddy:80** only (plus optional `127.0.0.1:9090` for auth-gateway during local bootstrap—never expose admin to the public internet without an additional control).
- Caddy upstream addresses use **internal** `http://<service>:<port>` (e.g. `http://naabu-mcp:8105`). After `uri strip_prefix /naabu-mcp`, the upstream path should match what **FastMCP** expects for `MCP_TRANSPORT=streamable-http` (typically `/mcp/`). Confirm with one server’s README if a server uses a non-default root.

#### 12.1.B `port-map.json` (generator input)

Single source of truth for compose services and `routes.conf`. Minimal example:

```json
{
  "servers": [
    { "name": "naabu-mcp", "port": 8105, "image": "hackerdogs/naabu-mcp:latest", "tier": "T0" },
    { "name": "trivy-mcp", "port": 8150, "image": "hackerdogs/trivy-mcp:latest", "tier": "T1" }
  ]
}
```

Add `tier` before P1. Reserve **8400–8499** for dynamically registered servers (per PRD).

#### 12.1.C Auth-gateway: `GET /verify` contract

Caddy **`forward_auth`** sends a request (e.g. `GET http://auth-gateway:9090/verify`) that must carry the client’s **`Authorization`** header. In each generated route use at least:

```caddyfile
forward_auth auth-gateway:9090 {
    uri /verify
    copy_headers Authorization
}
```

Later, add other headers the MCP servers need for pass-through (e.g. `X-Shodan-Api-Key`) to `copy_headers` so they reach the MCP container unchanged.

**`/verify` implementation steps:**

1. Parse `Authorization: Bearer <token>`. Missing/malformed → **401**.
2. Hash the raw token with **SHA-256** (fixed encoding—hex is typical), look up `api_keys.key_hash`. Not found → **401**.
3. If `is_active` is false or `expires_at` in the past → **401** or **403** (pick one policy; document it).
4. Apply **per-key rate limit** (sliding window); exceeded → **429** or **403** (Caddy treats non-2xx as auth failure—ensure your choice is intentional).
5. **Authorization check:** read the **original request URI** Caddy forwards (e.g. `X-Forwarded-Uri` / `X-Forwarded-Path`). First path segment → `server_key` (e.g. `naabu-mcp`). If **`scope_mode = restricted`**, require a row in **`api_key_mcp_grants`** for that key and **`platform_mcp_servers.server_key`**; if **`all_platform`**, allow any catalog server (still subject to tenant status). → else **403**.
6. On success return **200** (body may be empty). Append **audit** row: `key_id`, `server`, HTTP method, timestamp; never log the Bearer token or upstream `X-*` secrets.

**Database:** Use **PostgreSQL + TimescaleDB** (§7). Apply [`docs/schema/mcp-farm-timescaledb.sql`](./schema/mcp-farm-timescaledb.sql). For `/verify`, a single indexed lookup on `key_hash` remains sub-millisecond at the DB; pool size follows gateway worker count. *(SQLite + WAL is acceptable **only** for local dev if you mirror the same table shapes.)*

#### 12.1.D Caddy base `Caddyfile` and generated `routes.conf`

Static skeleton (matches PRD):

```caddyfile
{
    admin off
    auto_https off
}

:80 {
    handle /health {
        respond "OK" 200
    }
    handle /admin/* {
        reverse_proxy auth-gateway:9090
    }
    handle /services {
        reverse_proxy auth-gateway:9090
    }
    import /etc/caddy/routes.conf
}
```

Per-server generated block example:

```caddyfile
@naabu-mcp path /naabu-mcp/*
handle @naabu-mcp {
    forward_auth auth-gateway:9090 {
        uri /verify
        copy_headers Authorization
    }
    uri strip_prefix /naabu-mcp
    reverse_proxy naabu-mcp:8105
}
```

After P1, the last line becomes `reverse_proxy mcp-policy:9300` (or your L3 listener); L3 then forwards to `naabu-mcp:8105`.

**Reload:** when `routes.conf` changes, reload Caddy via its **admin API** (`POST /load` with JSON config) on a **loopback-only** socket, or your chosen signal—never expose unrestricted Caddy admin to the tunnel.

#### 12.1.E MCP over HTTP (JSON-RPC)

Hackerdogs images use **FastMCP** with **streamable HTTP** at **`/mcp/`** (trailing slash as deployed). Bodies are **JSON-RPC 2.0** (`initialize`, `tools/list`, `tools/call`, … depending on session phase).

Illustrative **raw** request (real clients negotiate session first):

```http
POST /naabu-mcp/mcp/ HTTP/1.1
Host: mcp.example.com
Authorization: Bearer hd_sk_…
Content-Type: application/json

{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
```

Use a full MCP client for end-to-end tests; use `curl` mainly for **401/403** and routing.

#### 12.1.F `cloudflared` (compose fragment)

```yaml
cloudflared:
  image: cloudflare/cloudflared:latest
  command: tunnel run
  environment:
    - TUNNEL_TOKEN=${TUNNEL_TOKEN}
  networks:
    - mcpfarm_internal
  depends_on:
    - caddy
```

In Cloudflare Zero Trust, map the public hostname to **`http://caddy:80`**. TLS terminates at Cloudflare; HTTP on the Docker bridge is normal between tunnel and Caddy.

#### 12.1.G Local dev without Cloudflare

1. Use **`docker-compose.override.yml`** (or a profile) to publish Caddy as **`127.0.0.1:8080:80`**.
2. Point clients at `http://127.0.0.1:8080/<server>/mcp/`.
3. Omit `cloudflared` when `TUNNEL_TOKEN` is unset.

#### 12.1.H Bootstrap admin `curl`

```bash
curl -sS -X POST "http://127.0.0.1:9090/admin/keys" \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"name":"dev-agent","scope_mode":"restricted","rate_limit_rpm":60,"mcp_grants":["naabu-mcp"]}'
```

*Example body reflects **§7** `scope_mode` + grants; align with your implemented admin API or [FARM-PRD §4.3](./FARM-PRD.md#43-complete-admin-api-reference) if it still documents legacy `scopes`.*

Use HTTPS and your tunnel hostname in production.

#### 12.1.I `generate-compose.py` — required outputs

The generator script (step 1.3) should, from `port-map.json`, produce at least:

1. **`docker-compose.yml`** (or fragment) service stanzas: each MCP server with `image`, `container_name`, `environment` (`MCP_TRANSPORT=streamable-http`, `MCP_PORT=<port>`), `networks`, **no** host `ports:`.
2. **`caddy/routes.conf`**: one `@<name> path /<name>/*` block per server with `forward_auth`, `uri strip_prefix /<name>`, `reverse_proxy <name>:<port>`.
3. **Deterministic ordering** so diffs are reviewable (sort server names).

On **dynamic registration**, the auth-gateway rewrites `routes.conf` and triggers Caddy reload—the generator is the bootstrap only.

**Dynamic servers + Docker socket:** mounting `/var/run/docker.sock` into `auth-gateway` enables `docker run` for new images; treat this as **critical** risk—read-only socket mount still allows container control; restrict who can call `/admin/*`, use strong `ADMIN_SECRET`, and audit every `POST /admin/servers`.

**P0 exit criteria:** L0–L2 and L4 work; every request is authenticated and scope-checked; audit log records access. L3 is still missing—**do not call this “GA” for internet-facing cyber tools.**

---

### 12.2 P1 — MCP policy plane (layer L3) — “security GA”

**Outcome:** Every MCP request passes through an **MCP-native** proxy that understands `tools/list` / `tools/call` and enforces **deterministic** policy before the tool container runs.

**Open source in this section:** exactly **one** of **PolicyLayer Intercept**, **mcpwall**, **IronCurtain**, **AvaKill**, or **ressl/mcp-firewall** (see **§12.0A** row L3). All further steps assume that container is in the Compose graph.

| Step | Action | Done when |
|------|--------|-----------|
| 2.1 | Select an **L3 implementation** (Apache-2.0-friendly options preferred for distribution): e.g. PolicyLayer Intercept, `mcpwall`, or IronCurtain-style proxy—see [FARM-PRD §12.4](./FARM-PRD.md#124-open-source-options). | License + ops model approved. |
| 2.2 | **Classify servers** into trust tiers **T0–T3** (§5); store tier in registry metadata or a `tier` field alongside each server in config. | Spreadsheet or YAML lists every server with a tier. |
| 2.3 | **Author policies** per tier: allowed tool names/patterns, argument regexes (URLs, IPs—block metadata IPs, loopback, RFC1918 unless allowed), rate limits for `tools/call`. | Policy files in git, reviewed. |
| 2.4 | Add **L3 container** to Compose; place it **between** authenticated traffic and MCP upstreams. **Rewire** Caddy so: after `forward_auth`, traffic goes to **L3**, and L3 proxies to the existing per-server upstream (or to Caddy internal routes—avoid loops; single clear path). | `tools/call` hits L3 logs. |
| 2.5 | Pass **identity context** into L3 if supported: key id, scopes, server name (headers or subrequest)—so policies can differ by key or scope without re-parsing bodies twice. | Integration test: same tool allowed for key A, denied for key B. |
| 2.6 | **Negative tests:** crafted `tools/call` with SSRF-like URL, disallowed tool name, oversize payload—expect **DENY** with normal MCP error surface. | Test script or CI job green. |
| 2.7 | **Audit:** extend logging so policy **decision + reason code** (internal) is stored; optional hash of tool args for forensics without storing full payloads. | Operator can answer “why was this denied?” |
| 2.8 | **Performance:** measure p95 latency added by L3 on hot path; keep under agreed budget (e.g. &lt;5–10 ms for trivial allow). | Documented in runbook. |

#### 12.2.A Topology: where L3 sits

**Preferred — single L3 hop (Compose-friendly):**  
`Client → Caddy (forward_auth) → L3 reverse proxy → correct MCP container`

L3 must **route by server name** parsed from the path (`/naabu-mcp/...`) or from a header you set in Caddy after matching (e.g. `X-Farm-Server: naabu-mcp` via `header` directive where supported). L3’s upstream table maps **server name → `host:port`** on the Docker network.

**Avoid:** `L3 → Caddy → MCP` (loop). L3 talks **directly** to `naabu-mcp:8105`, etc.

**Alternative — sidecar L3 per MCP server:** one policy container per tool server; Caddy targets the sidecar port. Higher operational cost; use only if the shared L3 cannot multiplex cleanly.

#### 12.2.B Passing identity into L3

Caddy **`forward_auth`** does not automatically attach auth **response** headers to the upstream request. Practical patterns:

1. **Internal validate API:** L3 calls `GET http://auth-gateway:9090/internal/validate` (or `POST` with same `Authorization`) on the **private** network only; response JSON includes `key_id`, `tenant_id`, **`scope_mode`**, allowed `server_key` list (or grant summary), `rate_limit_remaining`. Implement **network ACL** so this route is unreachable from the tunnel.
2. **Merge L2+L3** in one process (single FastAPI/Go service: verify + MCP proxy)—fastest to ship; split later if needed.
3. **JWT** minted by auth-gateway—only if you already operate a signing key rotation story.

#### 12.2.C Policy rules to implement first

| Family | Example |
|--------|---------|
| Tool allowlist | T3: allow only `list_findings`; deny all other `tools/call` names. |
| SSRF / metadata | Reject arguments that resolve to `169.254.169.254`, `metadata.google.internal`, `127.0.0.0/8`, RFC1918, link-local—unless an explicit operator allowlist entry exists. |
| Dangerous name patterns | Deny tools matching `*shell*`, `*exec*`, `*write*` for keys tagged read-only (encode tag in scope string or separate DB column). |
| Body size | Max JSON body **N MB** at L3 or L1. |
| Rate | Per-key cap on `tools/call` per minute in addition to L2 global key limit. |

#### 12.2.D JSON body L3 must understand (`tools/call`)

```json
{
  "jsonrpc": "2.0",
  "id": "r1",
  "method": "tools/call",
  "params": {
    "name": "run_scan",
    "arguments": { "target": "example.com", "ports": "80,443" }
  }
}
```

Extract `params.name` and `params.arguments` for decisions. For audit, store **SHA-256** of a canonical JSON encoding of `arguments` if you need forensics without retaining plaintext.

#### 12.2.E Negative test matrix (minimum)

| Case | Expected |
|------|----------|
| Valid token, allowed tool | Normal MCP success path |
| Valid token, disallowed tool | MCP JSON-RPC error (HTTP may still be 200—document behavior) |
| SSRF-like URL/host in args | Deny |
| Oversized body | 413 or JSON-RPC error |
| Missing Bearer | 401 at `forward_auth` |

#### 12.2.F Latency check

```bash
# Example load generator (install hey or use wrk)
hey -n 200 -c 10 -m POST \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
  "https://mcp.example.com/naabu-mcp/mcp/"
```

Run **with L3 disabled** vs **enabled**; compare p95 latency and error rate.

**P1 exit criteria:** L3 mandatory on all MCP routes; default-deny or strict allowlists for **T3** servers; GA allowed for external users subject to your risk review.

---

### 12.3 P2 — Advanced ingress (optional)

**Outcome:** Richer MCP routing, OAuth/JWKS, multiplexing, or **OPA** for complex Rego when YAML is insufficient.

**Open source in this section:** **Envoy** / **Envoy Gateway** / **Envoy AI Gateway** (step 3.1), **Open Policy Agent** (3.2), **Coraza** if attached at ingress (often with Envoy WASM—coordinate with **12.4** for body-limit WAF parity on Caddy-only paths). Map: **§12.0A** P2 rows.

| Step | Action | Done when |
|------|--------|-----------|
| 3.1 | Decide: **enhance Caddy** vs introduce **MCP-aware gateway** (e.g. Envoy AI Gateway) in **L1**, keeping L2 auth and L3 policy as separate concerns or merging carefully. | ADR written. |
| 3.2 | If using external **OPA**: extract policy from L3 or run sidecar; define stable **input JSON** (tenant, tool, args, tier). | Rego tests in CI. |
| 3.3 | Add **TLS** at edge if not solely via Cloudflare; rotate certs. | SSL Labs / internal scan acceptable. |

**Technical — OPA input document (illustrative):**

```json
{
  "key_id": "a1b2c3d4",
  "tier": "T2",
  "mcp_server": "trivy-mcp",
  "tool": "scan_image",
  "arguments": { "ref": "gcr.io/proj/image:tag" }
}
```

OPA package returns `{ "allow": true }` or `{ "allow": false, "reason": "tier_violation" }`; L3 maps `false` to an MCP-safe error.

**Envoy AI Gateway / MCP CRDs:** pin chart and container **image digest**; run upgrade tests—MCP routing CRDs are version-sensitive.

---

### 12.4 P3 — Content inspection (optional)

**Outcome:** Secret/PII detection and redaction on **selected** routes or tiers without blowing hot-path latency (async or sampled).

**Open source in this section:** **Microsoft Presidio**, **TruffleHog** (step 4.1); **Coraza** or equivalent **WAF** for HTTP/body abuse (4.2). These are **security controls** (DLP/WAF), not the **§12.6** telemetry stack—see **§12.0A** P3 rows.

| Step | Action | Done when |
|------|--------|-----------|
| 4.1 | Integrate **response scanning** (e.g. TruffleHog-style, Presidio-style) for **T1–T2** outputs. | Known test secret is redacted or blocked. |
| 4.2 | Add **WAF / size limits** for malformed HTTP or huge bodies at L1. | Fuzzing does not crash workers. |
| 4.3 | Define **ALLOW_WITH_REDACTION** behavior end-to-end (§4). | Documented for clients if behavior visible. |

**Technical — streaming and buffers:** MCP responses can be large streams. Any inspection middleware must use a **bounded buffer** (max bytes) or stream parsers; on exceed, choose **fail closed** (error) or **pass-through with risk flag**—document the choice. Never hold unbounded tool output in memory.

**WAF / body limits at L1:** set `client_max_body_size` equivalent in Caddy (`request_body` limits / `map` handlers) or terminate huge requests before auth to save CPU.

---

### 12.5 P4 — Runtime hardening (optional)

**Outcome:** Host and container runtime enforcement where you run **Linux** in production.

**Open source in this section:** **Falco** (5.3), **KubeArmor** (5.4, K8s). **§12.0A** P4 rows.

| Step | Action | Done when |
|------|--------|-----------|
| 5.1 | **seccomp / AppArmor / read-only root** on MCP containers. | Compose or security profile applied. |
| 5.2 | **Network policies** or equivalent: egress allowlists from MCP containers. | Egress to unexpected hosts fails. |
| 5.3 | Deploy **Falco** (or equivalent) on Linux nodes; alert on suspicious syscalls; route alerts to SIEM or on-call. | Alerts reach SIEM or inbox. |
| 5.4 **(optional)** | On **Kubernetes**, deploy **KubeArmor** (or equivalent LSM/eBPF enforcer) with policies aligned to **§9.6**; validate against representative MCP pods. | Violations blocked or alerted per policy. |

**Compose sketch (hardening knobs—validate per image):**

```yaml
naabu-mcp:
  image: hackerdogs/naabu-mcp:latest
  read_only: true
  tmpfs:
    - /tmp
  security_opt:
    - no-new-privileges:true
  # cap_drop: [ALL]   # enable only after proving the tool still runs
```

Many security CLIs need **extra caps** or writable cache dirs—**test** before enforcing `cap_drop` or strict `read_only`.

---

### 12.6 Observability stack (§8 — parallel with P0+)

**Outcome:** **Telemetry** for SRE—metrics, traces, optional centralized logs—per **§8** and **§9.7**. This track runs **alongside** P0–P1; it does **not** replace L2/L3. Components here are the **Observability plane** rows in **Architecture overview**.

| Step | Action | Done when |
|------|--------|-----------|
| 6.1 | Add **OpenTelemetry Collector** to Compose (or DaemonSet on K8s): OTLP receivers, processors (batch, attributes), exporters. | Collector `/` or health port OK; smoke span exported. |
| 6.2 | Instrument **auth-gateway** and **L3** with **OTel SDK** (or supported auto-instrumentation): spans around `/verify`, MCP proxy, DB pool; propagate **W3C trace context**; write **`client_request_id`** compatible with **§7** hypertables. | End-to-end trace across Caddy → gateway → DB visible in backend. |
| 6.3 | Deploy **Jaeger** (or **Grafana Tempo**) for traces; **Grafana** for dashboards; add **Prometheus**/Mimir and **Loki** if you split metrics/logs. Wire Collector exports. Dashboards: gateway QPS, p95, error ratio; optional **L3 deny count** from metrics (deny **reasons** remain in **`policy_event_log`**). | On-call runbook links dashboard → trace → `request_id`. |
| 6.4 **(optional)** | If **Timescale** is not enough for raw log search volume, add **ClickHouse** (or a warehouse) via Collector/vector; enforce **redaction** of secrets in exporters—**§8.2**. | Documented pipeline; cardinality controls in place. |

**Do not** place **Presidio** / **TruffleHog** here—they are **P3 controls** (**§12.4**).

---

### 12.7 Companion plane — LLM / agent guard (recommended for high risk)

**Outcome:** Defense for **prompt-layer** attacks that never appear clearly in MCP tool args.

**Open source in this section:** **InferShield**, **LlamaFirewall**, or **NeMo Guardrails** (pick one or combine per risk). **§12.0A** companion row. Deploy **outside** the farm MCP URL path.

| Step | Action | Done when |
|------|--------|-----------|
| 7.1 | Deploy **InferShield**, **LlamaFirewall**, or **NeMo Guardrails** **between** your agent app and the **LLM provider API** (see [FARM-PRD §12.5–12.7](./FARM-PRD.md#125-recommended-architecture-defense-in-depth)). | Injection test cases reduce unsafe tool-planning. |
| 7.2 | Optionally standardize a **security metadata envelope** on tool calls (agent id, session id, approval state) so L3 can enforce **step-up** without seeing full chat. | Documented contract for internal agents. |

**Technical — optional non-secret headers:** If the agent controls HTTP to the farm, it may send `X-Farm-Agent-Id`, `X-Farm-Session-Id` (opaque IDs, not JWTs unless validated). L3 policies can **require** these for T2+. Add them to Caddy `copy_headers` so they reach L3 and MCP servers. **Never** place upstream API secrets in these headers.

---

### 12.8 Scaling path (after single host works)

**Open source in this section:** **PostgreSQL** / **TimescaleDB** HA (8.1), **Redis** (8.2), load balancer of your choice (8.3), Timescale policies (8.4). No new products beyond **§12.0A** unless you add a managed DB or cloud LB.

| Step | Action | Done when |
|------|--------|-----------|
| 8.1 | **PostgreSQL + TimescaleDB** already shared by replicas; scale DB with your HA playbook (replicas, PgBouncer, managed Timescale). | Multiple auth-gateway containers use one DSN. |
| 8.2 | Put **shared rate-limit state** in **Redis** when horizontally scaling L2 (required for consistent sliding windows). | Limits align across replicas. |
| 8.3 | **Load-balance** multiple identical farm stacks behind edge LB; sticky sessions only if MCP transport requires it. | Health checks route around failures. |
| 8.4 | Tune **Timescale** `add_retention_policy` / `add_compression_policy` on `request_log` and `policy_event_log` for cost and query speed. | Old chunks drop or compress on schedule. |

**Technical — session stickiness:** Streamable HTTP / SSE may associate server-side session state with a connection. If you scale **Caddy** horizontally, use **consistent hashing** on a stable client key, **or** terminate MCP on one replica per deployment until your MCP stack is stateless at the transport layer—verify with your FastMCP version.

**Rate limits:** in-memory windows in a single auth-gateway process do **not** synchronize across replicas; use **Redis** for counters **before** running multiple gateway replicas.

---

### 12.9 Troubleshooting

| Symptom | Likely cause | What to check |
|---------|----------------|---------------|
| 401 everywhere | Bad token; `Authorization` not copied to `forward_auth` | Caddy `copy_headers Authorization`; DB `key_hash` algorithm matches issuance |
| 403 with “good” key | Grant / scope mismatch | Path `server_key` vs **`api_key_mcp_grants`** or **`scope_mode`**; trailing slashes |
| 502 / empty response | MCP container down; wrong internal port | `docker compose ps`; from a debug container `curl -v http://naabu-mcp:8105/mcp/` |
| Works locally, fails via tunnel | Tunnel origin misconfigured | Tunnel must target **`caddy:80`**, not an MCP service |
| New dynamic server 404 | Routes not loaded | Shared `routes.conf` volume; Caddy reload API success |
| L3 breaks streaming | Buffering | L3 must support HTTP streaming for MCP or document max buffer |
| Intermittent 429 | Rate limit too aggressive | Per-key limit vs burst; Redis clock skew if distributed |

---

### 12.10 Final checklist (“hero” bar)

- [ ] **L0–L4** running; **L3** enforcing tool policy on every MCP route  
- [ ] **§12.0A:** every OSS component you deployed is traceable to a completed step  
- [ ] **§12.6** (or waiver): OTel + trace backend for gateway/L3; Grafana or equivalent for SRE  
- [ ] **Scoped keys / grants**, rotation runbook, admin API-only management  
- [ ] **No inbound ports** on host (if using tunnel) or documented firewall rules  
- [ ] **Logs redacted**; **Docker socket** (if any) least-privilege and audited  
- [ ] **Trust tiers** and policies documented per server  
- [ ] **LLM/agent guard** deployed or explicitly waived with sign-off  
- [ ] **Disaster recovery:** Postgres/Timescale backups (volume or managed snapshots), tunnel token rotation procedure  

---

## 13. Summary

The **AI-aware zero-trust gateway for MCP** is the **name and topic of the main spec**: a **layered** system (§3) that treats every tool call as **untrusted until proven compliant**, understands **MCP semantics**, and scales from **one Compose deployment** to **defense-in-depth** (§9 P2–P4). **§7** defines the **tenant data plane and durable audit**; **§8** separates **telemetry and SRE observability** from **preventive controls**. **§12** is the implementation guide; **§12.0A** maps each **Architecture overview** OSS product to a **numbered step**.
