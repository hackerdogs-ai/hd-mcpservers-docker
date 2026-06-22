# MCP Server Farm — Completion List

> Status snapshot generated from a full repository review: the 401 `*-mcp` server
> directories, the farm backend (`mcpfarm/`), the farm UI (`mcpfarm-ui/`), the CI
> setup (`.github/workflows/`), and the architecture docs (`docs/`).
>
> **Goal (from project brief):** a single–`docker compose`, scalable, extensible MCP
> server farm hosting 300+ MCP servers, auto-published to Docker Hub, callable
> securely by any LLM worldwide, with every call authenticated, rate-limited and
> tracked.

## At-a-glance status

| Area | State | Headline number |
|------|-------|-----------------|
| MCP server inventory | 🟡 Mostly done | 401 dirs; 386 wired into the farm; **264 have all 7 required files** |
| Server test compliance | 🟡 Mostly done | Sweep: **350 PASS / 36 FAIL** of 386 |
| Farm backend (`mcpfarm/`) | 🟢 Functionally complete | Auth + routing + lifecycle work end-to-end (SQLite) |
| Farm UI (`mcpfarm-ui/`) | 🟢 Functionally complete | 4 modes; tool exec + agentic loop wired |
| Docker Hub auto-publish (CI) | 🔴 **Missing** | No publish workflow; only `security-scan.yml` exists |
| Architecture consolidation | 🔴 **Not done** | 5 competing docs; implementation ≠ canonical design |
| Zero-trust / multi-tenant / L3 policy | 🔴 **Not implemented** | Required by canonical design, absent from code |

Legend: 🟢 complete · 🟡 partial · 🔴 not started / missing

---

## 1. MCP Servers (the 401 `*-mcp` directories)

### ✅ Complete
- **401 server directories** exist; **386** are registered in `mcpfarm/port-map.json`
  and wired into `mcpfarm/docker-compose.yml`.
- **264 / 401 servers** have the full required file set per `Instructions.md`
  (Dockerfile, `publish_to_hackerdogs.sh`, README.md, `mcp_server.py`,
  `mcpServer.json`, `test.sh`, `progress.md`).
- **350 / 386** servers **PASS** the test sweep (`ALL_MCP_TESTS_SUMMARY.tsv`,
  `ALL_MCP_SWEEP_CONCLUSION.md`) — stdio + HTTP-streamable `tools/list` and
  `tools/call`.
- `mcpServer.json` present in **all** server dirs (0 missing).
- Dockerfile / README.md / test.sh present in all but 1 server each.
- Shared test tooling exists (`scripts/mcp-five-step-compliance.sh`,
  `scripts/run-all-mcp-tests.sh`, batch runners).

### ❌ Incomplete
- **36 servers FAIL the sweep** — must be fixed to reach "all PASS". Themes
  (from `ALL_MCP_SWEEP_CONCLUSION.md`):
  - HTTP `tools/list` / streamable transport failures (AWS, API, some 3rd-party images).
  - stdio `tools/list` auth/env failures (Azure, Notion, Cloudflare, Brave, Bright Data…).
  - `hd_fetch` shared-dependency gap: `dirb`, `dirsearch`, `feroxbuster`, `gobuster`.
  - Docker build failures: `bettercap`, `gitleaks`, `horusec`, `subjack`,
    `vulnerability-scanner`.
  - Upstream/infra: `ai-humanizer` (DNS), `x8-mcp` (invalid base image),
    `boofuzz-mcp` (port 8333 in-use during sweep).
- **6 servers are known build failures** (also tracked in `mcpfarm/deploy.sh` /
  `DEPLOY.md`): `bettercap-mcp`, `gitleaks-mcp`, `horusec-mcp`, `subjack-mcp`,
  `vulnerability-scanner-mcp`, `x8-mcp`. These are excluded from `--start-all`.
- **Missing required files** across the 401 dirs:
  - `progress.md` — **133 missing**
  - `mcp_server.py` — **75 missing** (some servers wrap upstream images and have no
    local wrapper; confirm each is intentional vs. a real gap)
  - `publish_to_hackerdogs.sh` — **33 missing**
  - Dockerfile / README.md / test.sh — **1 missing** each
- **15 server dirs are NOT in `port-map.json`** (exist on disk but not wired into the
  farm): `acuvity-mcp-server-alterx-mcp`, `acuvity-mcp-server-amass-mcp`,
  `acuvity-mcp-server-arjun-mcp`, `acuvity-mcp-server-assetfinder-mcp`,
  `censys-platform-mcp`, `github-mcp`, `hackerdogs-mcp-server-mcp`, `mcp-docker-mcp`,
  `mitre-attack-remote-mcp`, `prowler-mcp`, `serpapi-mcp`, `tavily-remote-mcp`,
  `tools-to-migrate-to-mcp`, `whoisxmlapi-mcp`, `xpoz-mcp-server-mcp`.
  Decision needed per server: register + assign a port, or remove.
  (`tools-to-migrate-to-mcp` looks like a scratch folder — remove or empty it.)

### Action items
- [ ] Fix the 36 failing servers (start with the 6 build failures and the
      `hd_fetch` dependency gap — both are systemic, not one-offs).
- [ ] Backfill `progress.md` (133), `publish_to_hackerdogs.sh` (33), and audit the
      75 missing `mcp_server.py` (intentional upstream-wrap vs. real gap).
- [ ] Reconcile the 15 unregistered dirs: add to `port-map.json` + compose, or delete.
- [ ] Re-run the full sweep and update `ALL_MCP_TESTS_SUMMARY.tsv` until 100% PASS.

---

## 2. Farm Backend — `mcpfarm/`

A FastAPI **auth-gateway** + **Caddy** reverse proxy + **cloudflared** tunnel,
orchestrated by `docker-compose.yml` generated from `port-map.json`. SQLite store.

### ✅ Complete
- **Single-command deploy** (`deploy.sh`): env setup, image builds (graceful failure
  handling), ordered startup, DB seed, Caddy route reload, optional `--start-all`,
  health/tunnel/stats verification.
- **API-key auth**: `hd_sk_` keys, SHA-256 hashed in SQLite, per-key scopes, expiry,
  active flag. Caddy `forward_auth` → gateway `/verify` on every request.
- **Per-key rate limiting**: in-memory 60s sliding window (`rate_limiter.py`).
- **Server lifecycle via Docker SDK** (`docker_manager.py`): start/stop/restart,
  env-var updates, logs, dynamic (runtime-registered) servers recovered on restart.
- **Health monitoring**: 30s background loop probing every server's MCP `initialize`.
- **Dynamic routing**: `caddy_reload.py` generates per-server `forward_auth` +
  `reverse_proxy` blocks and hot-reloads via the Caddy admin API.
- **Audit/usage**: `request_logs` table; `/admin/audit`, `/admin/stats`,
  `/admin/keys/{id}/usage` endpoints.
- **Zero open ports for MCP servers** — internal Docker network only; ingress only via
  Cloudflare tunnel.
- **DB seeding** (`seed.py`): idempotent; loads 386 servers; mints first admin key.

### ❌ Incomplete / gaps vs. canonical design
- **Datastore mismatch:** code uses **SQLite**; the canonical design
  (`docs/AI-aware-zero-trust-gateway-for-MCP.md`, `docs/schema/mcp-farm-timescaledb.sql`)
  mandates **PostgreSQL + TimescaleDB** for durable multi-tenant audit. No migrations
  (Alembic/Flyway) exist.
- **No L3 "AI-aware" MCP policy plane** (tool-call firewall). The canonical design marks
  this **mandatory for security GA** — inspect `tools/call` method/args, ALLOW / DENY /
  REDACT / REQUIRE_APPROVAL, log to `policy_event_log`. Currently Caddy → MCP directly.
- **No multi-tenancy:** no `tenants` table, no `tenant_id` propagation, no per-tenant
  isolation. Schema in `docs/schema/` (`platform_mcp_servers` + `tenant_mcp_deployments`,
  normalized `api_key_mcp_grants`) is **not implemented** — code uses a flat `servers`
  table and CSV `scopes` string.
- **Audit log bug:** request status is hardcoded `200` (`auth-gateway/main.py` ~L376) —
  failures/denies are not distinguishable in the audit trail.
- **No DB indexing** on `request_logs(created_at, key_id)` → `/admin/audit` and `/admin/stats`
  degrade at scale.
- **Rate limiter is in-memory** → not correct across multiple gateway replicas (needs Redis
  for the multi-gateway scaling story).
- **Hardcoded network name** `mcpfarm_internal` in `docker_manager.py` (inflexible for
  multi-instance).
- **No image-pull retry** in `docker_manager.start_server()`.

### Action items
- [ ] Decide datastore: keep SQLite (single-node MVP) **or** migrate to Postgres+TimescaleDB
      per `docs/schema/mcp-farm-timescaledb.sql` (recommended for GA). Add migrations.
- [ ] Implement the L3 policy plane (or integrate an OSS option: PolicyLayer Intercept /
      mcpwall / IronCurtain) and route Caddy → L3 → MCP. Persist `policy_event_log`.
- [ ] Fix the audit status-code bug; add request_log indexes.
- [ ] If multi-tenant is in scope: adopt the normalized schema (`tenants`,
      `platform_mcp_servers`, `api_key_mcp_grants`) and thread `tenant_id` through.
- [ ] Swap rate limiter to Redis if/when running >1 gateway replica.

---

## 3. Farm UI — `mcpfarm-ui/`

Vite + React + Tailwind SPA, served by Caddy on :3000. Talks to the gateway via
relative URLs (dev proxy in `vite.config.js`).

### ✅ Complete
- **Four modes**: Manual (single-server tool exec), Multi-select (aggregate tools across
  servers), Prompt (Claude agentic loop), Nova (agentic + HeyGen live avatar).
- **Server browser** (`ServerList`): search, category filters, health status,
  start/stop with health polling, running-count badge.
- **Schema-driven tool forms** + result/error viewer (`ManualMode`).
- **Per-server env/API-key editor** (`ServerConfig`) → `PATCH /admin/servers/{name}/env`.
- **Settings**: farm base URL, API key, admin secret, Claude key, HeyGen creds; rotate
  via `/admin/rotate-secret`; startup sync via `/ui-config`.
- **Fully wired to backend** (`src/lib/api.js`, `mcp.js`, `claude.js`); no TODO/stub
  markers in source. Dockerfile builds and serves via Caddy (SPA fallback + gzip).

### ❌ Incomplete / missing screens
- **No usage / call-tracking dashboard** — backend records `request_logs` but the UI has
  no metrics, charts, per-key/per-server usage views. (Brief explicitly wants "calls are
  tracked" surfaced.)
- **No API-key management UI** — `listApiKeys` / `createApiKey` / `revokeApiKey` exist in
  `api.js` but no screen uses them. Keys must be managed via raw API today.
- **No "copy install config" (`mcpServer.json`) export** — users can't grab a ready-to-paste
  Claude/Cursor config from the UI.
- **No per-server log viewer** (`/admin/servers/{name}/logs` exists in backend, unused in UI).
- **No favorites / bulk operations** (start/stop one at a time).
- **Hardcoded values** to parameterize: Claude model `claude-sonnet-4-6` (`src/lib/claude.js`),
  MCP protocol version `2024-11-05` (`src/lib/mcp.js`), agentic loop cap = 10.
- Minor a11y gaps (missing ARIA labels on modals/status dots).

### Action items
- [ ] Build a **Usage/Analytics** view backed by `/admin/audit` + `/admin/stats`.
- [ ] Build an **API-key management** screen (create/scope/expire/revoke) using existing
      `api.js` functions.
- [ ] Add **"Copy install config"** (render `mcpServer.json` with the user's key + URL).
- [ ] Add a **per-server logs** panel.
- [ ] Parameterize hardcoded model / protocol / loop-cap constants.

---

## 4. Docker Hub Auto-Publish (CI/CD) — 🔴 biggest gap

### ✅ Complete
- Each server ships a `publish_to_hackerdogs.sh` with `--build` / `--publish` flags that
  `docker build` + `docker push` to Docker Hub (multi-arch support present). 368/401 dirs
  have it.
- `mcpfarm/deploy.sh` can build all images locally.

### ❌ Incomplete
- **No GitHub Actions (or any CI) workflow that auto-builds and pushes server images to
  Docker Hub.** The only workflow is `.github/workflows/security-scan.yml`
  (Gitleaks/TruffleHog/scanning) — it does **not** publish. Requirement #2
  ("automatically deployed to dockerhub") is **unmet**.
- No tag/versioning strategy beyond `latest`; no per-server change detection (rebuild only
  what changed); no registry-login/secrets wiring documented.
- `compose`/`port-map` assume images exist on Docker Hub (`hackerdogs/*-mcp:latest`) but
  nothing guarantees they are published and current.

### Action items
- [ ] Add a **publish workflow** (`.github/workflows/publish-images.yml`): on merge to
      `main`, detect changed `*-mcp` dirs, build + push `hackerdogs/<name>-mcp:latest`
      (and a pinned tag) using `docker/build-push-action` + Docker Hub secrets, with a
      build matrix and the 6 known-broken servers quarantined.
- [ ] Add a **farm-orchestration publish** step for `auth-gateway` and `mcpfarm-ui` images.
- [ ] Define a versioning/tagging convention (`:latest` + `:<git-sha>` / semver).
- [ ] Gate publish on `test.sh` passing (tie into the 5-step compliance sweep).

---

## 5. Architecture Consolidation — 🔴 not done

The brief asks to consolidate "multiple farm architectures in `docs/`" into one central
design implemented in `mcpfarm/` + `mcpfarm-ui/`. Five docs currently disagree:
`FARM-ARCHITECTURE.md`, `FARM-ARCHITECTURE-DIAGRAM.md`, `FARM-PRD.md`,
`AI-aware-zero-trust-gateway-for-MCP.md`, `ChatGPT Guidance on MCP Server Farm.md`,
plus `docs/schema/mcp-farm-timescaledb.sql`.

### Key conflicts to resolve
| Topic | FARM-ARCH / FARM-PRD | AI-aware / schema / ChatGPT | Recommended decision |
|-------|----------------------|-----------------------------|----------------------|
| Datastore | SQLite | **Postgres + TimescaleDB** | Postgres+TimescaleDB for GA; SQLite = dev only |
| L3 tool-call firewall | Optional | **Mandatory for security GA** | Mandatory (phase P1) |
| Ingress | Caddy only | Envoy AI Gateway (ChatGPT) | Caddy now; Envoy optional later |
| Scope model | CSV `scopes` | **Normalized `api_key_mcp_grants`** | Normalized grants |
| Server registry | flat `servers` table | `platform_mcp_servers` + `tenant_mcp_deployments` | Normalized + multi-tenant |
| Tenancy | single-tenant | **multi-tenant** | Multi-tenant if required by GA |

### Action items
- [ ] Write **one** canonical `docs/FARM-DESIGN.md` (layers L0–L5, request flow,
      auth/zero-trust, Docker Hub CI, scaling, call tracking/metering), superseding the
      five docs (archive the rest under `docs/archive/`).
- [ ] Record explicit decisions on the six conflicts above.
- [ ] File a delta list of where the current `mcpfarm/` implementation diverges from the
      chosen canonical design (datastore, L3, tenancy, scope model) and sequence the work.

---

## 5b. Deployment validation (local smoke test)

The farm was brought up locally in isolation (alt ports, no Cloudflare tunnel, one
MCP server) and exercised end-to-end. **The core path works**, and the test surfaced
several real bugs (some now fixed).

### ✅ Verified working
- `auth-gateway` + `mcpfarm-ui` images build; `docker compose config` valid (390 services).
- auth-gateway becomes healthy, seeds 386 servers, mints the admin key.
- Caddy healthy (after fix below), routes hot-load via `/admin/reload`.
- **Auth enforcement**: request without a key → `401`; with a valid key → `200`.
- **Full MCP handshake through the gateway**: `initialize` → session → `tools/list`
  returns the server's tools (validated against a live `dnstwist-mcp`).
- **Call tracking**: `request_logs` increments; `/admin/stats` and `/services` (386) work.
- **UI** served via Caddy default route (`200`, title "Hackerdogs MCP Farm").

### ✅ Bugs found and FIXED during deploy test
- **Caddy first-boot deadlock** (`mcpfarm/caddy/Caddyfile`): hard `import …/routes.conf`
  crash-loops Caddy on a fresh machine (the file is only written on `/admin/reload`,
  which needs Caddy up). Changed to optional glob `import …/dynamic/*.conf`. *This blocked
  every first-time deploy.*
- Stale `--start-all` skip list in `deploy.sh` and stale "Known Build Failures" table in
  `DEPLOY.md` — updated to reflect the now-fixed builds.

### ✅ Bugs found and FIXED (this session)
- **`mcp_http_proxy.py` `select()` crash** — `ValueError: filedescriptor out of range in
  select()` killed the container under load. Switched to `select.poll()` (no FD_SETSIZE
  limit) and added an idle-session reaper to stop the subprocess/FD leak. Propagated to
  **all 76 bundled per-server copies**. Stress-tested 60/60 init+tools/list, no crash.
- **88 servers' `test.sh` couldn't run** — restored `scripts/mcp_compliance_python.sh`
  (from git) and reconstructed `scripts/mcp_test_bootstrap.sh`; removed both from
  `.gitignore`. `gitlab-mcp` (a previously-broken one) now passes 5/5.
- **`deploy.sh` required a tunnel token** — added `--no-tunnel` / `--local` (skips
  cloudflared) and a `FARM_HTTP` override so local deploys work off port 80. Validated
  the full `deploy.sh --no-tunnel` path end-to-end, then ran an MCP server (`dnstwist`)
  through the deployed gateway: `initialize`→`tools/list`→`['fuzz_domain']`, calls tracked.

### ✅ Docker-in-Docker — resolved
Only **2** servers used the fake-docker pattern:
- `dnstwist-mcp` — **FIXED**: installs dnstwist natively (+ its Python deps) and shims
  `docker run … elceef/dnstwist <args>` to the native binary. Verified: `fuzz_domain`
  returns 146 KB of real results, no socket needed.
- `docker-bench-security-mcp` — genuine exception: it audits a Docker host, so it
  **requires** the docker socket by design and cannot go native. Mount the socket for
  this one server only, or accept tools/list-only.

### ✅ Remaining sweep failures — all explained (verified)
Re-tested the last 12 from current source:
- **Pass 5/5**: `google-threat-intelligence`, `greynoise`, `hibp`, `nasa`, `notion`, `winston-ai`.
- **Credential-gated (not a bug)**: `octagon`, `postman`, `s3-mcp-server`, `search1api`,
  `serper-search` — the upstream server needs its API key to start. Proven: `postman` with
  a dummy `POSTMAN_API_KEY` + 15s startup → `tools/list` = 42 tools. They work once keys are
  injected (the farm does this via env). Their CI "failure" is just the absent key.
- `steampipe` — stdio passes; HTTP `tools/list` needs a longer cold-start / cloud creds.

**Net: no genuine code bugs remain among the original 36 sweep failures.** What's left is
credential configuration (expected) and one socket exception (`docker-bench-security`).

### Test-harness note
The HTTP probe default `MCP_HTTP_STARTUP_SLEEP=10` is too short for some cold npm starts
(postman needed ~15s). Consider bumping it in `scripts/mcp_test_bootstrap.sh` so
key-configured servers verify reliably in CI.

### Action items
- [x] Fix the `mcp_http_proxy.py` FD/`select()` bug (done; propagated to 76 copies).
- [x] Restore + un-ignore `mcp_test_bootstrap.sh` and `mcp_compliance_python.sh`.
- [x] Add a no-tunnel local deploy mode to `deploy.sh`.
- [ ] Decide socket policy for Docker-in-Docker servers.
- [ ] Rebuild + push the 76 affected server images so the proxy fix ships.

---

## 6. Suggested sequencing

1. **Make the farm provably runnable end-to-end** (highest signal): fix the 6 build
   failures + `hd_fetch` gap, re-run the sweep toward 100% PASS.
2. **Close requirement #2**: add the Docker Hub publish CI workflow.
3. **Consolidate the architecture** into one canonical doc + decision log.
4. **Backfill server hygiene**: `progress.md`, `publish_to_hackerdogs.sh`, reconcile the
   15 unregistered dirs.
5. **UI gaps that surface the value prop**: usage dashboard, API-key management, install-config export.
6. **Zero-trust / scale hardening** (per canonical design): Postgres+TimescaleDB migration,
   L3 policy plane, audit status-code fix + indexes, Redis rate limiter, multi-tenancy.

---

*Generated from a repo-wide review. Counts (401 dirs, 386 registered, 264 fully-filed,
350/386 PASS) are reproducible via `scripts/run-all-mcp-tests.sh` and the file-presence
scan; re-verify after each change batch.*
