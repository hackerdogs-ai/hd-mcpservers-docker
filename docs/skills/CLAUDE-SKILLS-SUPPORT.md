# Claude Skills Support in the MCP Farm — PRD & Technical Spec

**Status:** Draft — proposed design
**Owner:** Farm / Platform
**Updated:** 2026-07-24
**Scope:** Add first-class support for **Claude Agent Skills** to the Hackerdogs MCP Server Farm so that, alongside the 400+ MCP servers, the farm can host, index, secure, serve, and consume **Skills** through the same gateway, UI, and chat surfaces.

**Related docs:**
- Canonical gateway design: [`../AI-aware-zero-trust-gateway-for-MCP.md`](../AI-aware-zero-trust-gateway-for-MCP.md)
- Farm PRD (archived): [`../FARM-PRD-old.md`](../FARM-PRD-old.md)
- Deploy runbook: [`../../mcpfarm/DEPLOY.md`](../../mcpfarm/DEPLOY.md)
- Chat assistant / vector design: [`../chat-assistant-ui.md`](../chat-assistant-ui.md)

> **Reading guide.** §1–§6 are the **PRD** (why, who, what). §7–§15 are the **technical spec** (how). §16–§19 cover rollout, security, success criteria, and open questions. **§20 is a basic→advanced FAQ** (start here for "what is a skill?" and "where do scripts run?"). Appendices A–E contain concrete schemas, payloads, and examples.

---

## 1. Executive summary

The farm today is a registry of **MCP servers** — running containers that expose *tools* (executable functions) over `streamable-http` behind a Caddy + auth-gateway zero-trust proxy. **Claude Skills** are a different, complementary primitive: they are **not** running services but **packaged instructions** (a `SKILL.md` file plus optional bundled `scripts/`, `references/`, and `assets/`) that teach an agent *how* to perform a task and *when* to do it.

This spec proposes making Skills a first-class farm citizen:

- A **Skills registry** parallel to the server registry (DB table, admin API, public catalog).
- A **skill package format** and validator that mirrors the open [`agentskills.io/specification`](https://agentskills.io/specification) (which Anthropic authored).
- **Three delivery mechanisms**, because Skills — unlike MCP — have no single network protocol:
  1. **`skills-mcp`** — an MCP server that exposes skills to *any* MCP client as MCP **resources/tools** (fits the farm's existing zero-trust path with zero client changes).
  2. **Bundle sync** — authenticated download of a skill as a `.zip`/`.tar.gz` for filesystem-based agents (Claude Code, Cursor, the Claude Agent SDK) that read `.claude/skills/`.
  3. **Native chat** — the farm's own Chat page performs **progressive disclosure** server-side (inject skill metadata into the system prompt, load the body on trigger, execute bundled scripts in a sandbox).
- **Vector-index** integration (new `doc_type: "skill"`) so skills are discoverable in the same semantic search that powers the chat assistant.
- A **UI Skills tab** modeled on the existing Catalog/Marketplace.
- A **security model** for the fact that skills can carry executable code and request tool access (`allowed-tools`), integrated with the existing tool-call firewall (L3) roadmap.

The design principle matches the rest of the farm: **skills are transparent infrastructure**. A user points a client at the farm, provides a Bearer token, and skills "just work" — either surfaced through MCP, synced to disk, or applied by the farm's own agent.

---

## 2. Background: what is a Claude Skill?

A **Skill** is a directory containing at minimum a `SKILL.md` file. The file has two parts: **YAML frontmatter** (metadata) and a **Markdown body** (instructions). Optional subdirectories bundle supporting files.

### 2.1 Directory structure

```
skill-name/
├── SKILL.md            # required — YAML frontmatter + Markdown instructions
├── scripts/            # optional — executable code for deterministic/repetitive tasks
├── references/         # optional — docs loaded into context on demand
└── assets/             # optional — templates, icons, fonts used in output
```

### 2.2 `SKILL.md` frontmatter fields

Per the open specification (authored by Anthropic, mirrored at `agentskills.io/specification` and `code.claude.com/docs`):

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | **Yes** | 1–64 chars. Lowercase `a-z`, `0-9`, hyphens only. No leading/trailing hyphen, no `--`. **Should match the parent directory name.** Must not contain XML tags or the reserved words `anthropic` / `claude`. |
| `description` | **Yes** | 1–1024 chars, non-empty. Must state **both what the skill does and when to use it**; include trigger keywords/file types. No XML tags. This is the **primary routing signal**. |
| `license` | No | License name or reference to a bundled license file. |
| `compatibility` | No | ≤500 chars. Environment requirements (intended product, system packages, network access). e.g. `Requires git, docker, and jq`. |
| `metadata` | No | Arbitrary key→value map (e.g. `author`, `version`). |
| `allowed-tools` | No | *(Experimental)* Space-separated pre-approved tools, e.g. `Bash(git:*) Read`. Honored by Claude Code CLI; **not** applied by the Agent SDK (SDK controls tools via its own `allowedTools`). |

**Minimal example:**

```markdown
---
name: pdf-processing
description: Extract PDF text, fill forms, and merge files. Use when handling PDFs or when the user mentions PDFs, forms, or document extraction.
---

# PDF Processing

## Instructions
[step-by-step guidance for the agent]

## Examples
[concrete usage examples]
```

### 2.3 Progressive disclosure (the core design principle)

Skills load in **three levels** so they cost almost nothing until relevant:

| Level | What loads | When | Budget |
|-------|-----------|------|--------|
| **1 — Metadata** | `name` + `description` | Always, at startup, in the system prompt | ~100 tokens/skill |
| **2 — Instructions** | Full `SKILL.md` body | When the description matches the task | < ~5k tokens recommended (keep body < 500 lines) |
| **3 — Resources** | `scripts/`, `references/`, `assets/` files | Only when explicitly referenced/needed; scripts can *execute* without being read into context | As needed |

This is the property the farm must preserve when it serves skills: **advertise cheaply, hydrate on demand.**

### 2.4 How consuming agents use skills today

- **Claude Code CLI / Claude apps:** discover skills from `.claude/skills/` (project) and `~/.claude/skills/` (personal); load metadata at startup; invoke via the built-in **Skill** tool.
- **Claude Agent SDK (`query()`):** the `skills` option controls which discovered skills are enabled; the SDK adds the `Skill` tool to `allowedTools`. `settingSources: ["user", "project"]` loads skills from the filesystem.
- **Other agents (Cursor, custom):** read the same `SKILL.md` convention; the format is the "common denominator".

**Key takeaway for the farm:** skills are a **filesystem + agent-runtime** concept, not a wire protocol. The farm's job is to be the **distribution, governance, and discovery** plane for skills, then deliver them into whichever runtime the user has.

---

## 3. Skills vs MCP servers

| Dimension | MCP server (today) | Claude Skill (new) |
|-----------|--------------------|--------------------|
| **What it is** | A running container exposing *tools* | A packaged folder of *instructions* + optional code |
| **Runtime in farm** | Long-lived Docker container on `mcpfarm_internal` | **No process** — static content at rest (served on demand) |
| **Primitive** | `tools/list`, `tools/call` (JSON-RPC) | `name`/`description` + Markdown body + files |
| **Transport** | `streamable-http` at `/{name}/mcp` | Files: MCP resources, bundle download, or filesystem sync |
| **Consumed by** | MCP client makes tool calls | Agent reads instructions, then acts (may call tools/scripts) |
| **Cost when idle** | RAM/CPU per container | ~0 (bytes on disk); ~100 tokens metadata when advertised |
| **Auth** | Bearer token at Caddy `forward_auth` | Same Bearer token; per-skill scopes |
| **Discovery** | `/services`, vector index (`server`/`tool`/`readme` docs) | `/skills`, vector index (`skill` docs) |
| **Health** | `/mcp/` probe every 30s | Validation on upload (schema + lint), no liveness needed |
| **Risk surface** | Tool executes real commands | Instructions can *direct* tool use; bundled `scripts/` can execute; `allowed-tools` requests capabilities |

**They compose.** A skill often *orchestrates* MCP tools: e.g. a `recon-workflow` skill's body says "use `naabu-mcp` to scan, then `httpx-mcp`, then summarize." The farm is uniquely positioned to ship both halves together.

---

## 4. Goals & non-goals

### 4.1 Goals

| Goal | Description |
|------|-------------|
| **First-class registry** | Skills are stored, versioned, validated, and managed like servers — via admin API and UI. |
| **Spec-compliant** | Accept/validate any standards-compliant skill (`agentskills.io` spec); round-trip without loss. |
| **Zero-trust delivery** | All skill access flows through Caddy + auth-gateway (Bearer token, scopes, rate limit, audit) — same as MCP. |
| **Multi-runtime** | Deliver skills to MCP clients, filesystem agents (Claude Code/Cursor/SDK), and the farm's own chat. |
| **Progressive disclosure preserved** | Metadata is cheap; body and resources hydrate on demand across every delivery path. |
| **Semantic discovery** | Skills participate in the existing Redis vector search and chat assistant. |
| **Composable with servers** | Skills can reference farm MCP servers; bundles can ship a matching `mcp.json`. |
| **Safe by default** | Executable content is sandboxed; `allowed-tools` requests are policy-checked; supply-chain controls on upload. |
| **Transparent** | Users need no new concepts beyond "install a skill"; the farm plumbing is invisible. |

### 4.2 Non-goals (v1)

- Authoring/editing skills *inside* the farm UI (v1 is upload/import + view; an in-browser editor is a later phase).
- Executing arbitrary skill `scripts/` on the **farm host** for external clients (execution belongs to the consuming agent runtime; the farm only executes scripts inside its **own** sandboxed chat agent — see §11).
- Replacing MCP. Skills augment, not supersede, the server catalog.
- A public, unauthenticated skills marketplace (all access is gated by the farm's existing auth).

---

## 5. Personas & user stories

- **Security engineer (MCP client user):** "I want the farm's `web-recon` skill available in Cursor so my agent follows our approved recon methodology using farm tools." → installs `skills-mcp` **or** syncs the bundle.
- **Farm operator/admin:** "I want to upload, validate, scope, enable/disable, and audit skills the same way I manage servers." → admin API + UI Skills tab.
- **Farm chat user:** "I open the farm Chat, ask a question, and the right skill silently guides the answer." → native progressive disclosure in `chat_proxy`.
- **Agent/automation (SDK):** "My CI agent should pull the current, approved set of skills from the farm before a run." → authenticated bundle/manifest endpoint.

**Representative stories**

1. As an admin I can `POST /admin/skills` a `.zip` and get back a validation report + registered skill.
2. As a user I can `GET /skills` to list every enabled skill (name, description, version, category, scopes).
3. As an MCP client I can connect to `skills-mcp` and see each skill as a resource I can read (metadata first, body/resources on demand).
4. As a Claude Code user I can run a sync command that writes approved skills into `~/.claude/skills/`.
5. As a chat user, when I ask "audit this S3 bucket," the farm loads the `cloud-audit` skill body automatically and follows it.
6. As an admin I can disable a skill instantly and it disappears from all delivery paths.

---

## 6. Functional requirements

### 6.1 Registry & lifecycle
- **FR-1** Upload a skill as a `.zip`/`.tar.gz` (or register from a Git URL) with server-side validation.
- **FR-2** Validate `SKILL.md` against the spec (see §8.2). Reject on hard errors; warn on soft issues.
- **FR-3** Store multiple **versions**; one is marked `active`.
- **FR-4** Enable/disable/delete a skill; changes reflect in all delivery paths and the vector index immediately.
- **FR-5** Categorize skills reusing the existing category taxonomy (`vector_indexer.CATEGORY_LABELS`).
- **FR-6** Per-skill **scopes** honored by the same Bearer-token check used for servers.

### 6.2 Discovery
- **FR-7** Public (Bearer-gated) `GET /skills` listing with metadata only (Level-1 cheap).
- **FR-8** `GET /skills/{name}` returns full metadata + file manifest; `GET /skills/{name}/SKILL.md` returns the body; `GET /skills/{name}/files/{path}` returns a bundled resource.
- **FR-9** Skills indexed into the Redis vector store as `doc_type: "skill"` and surfaced by `/vectors/search` and the chat assistant.

### 6.3 Delivery
- **FR-10** `skills-mcp` server exposes skills as MCP resources (+ a `list_skills` / `get_skill` tool) to any MCP client.
- **FR-11** Authenticated bundle download (`GET /skills/{name}/bundle`) and a farm-wide **manifest** (`GET /skills/manifest.json`) for sync tooling.
- **FR-12** The farm Chat (`chat_proxy`) advertises Level-1 metadata for enabled skills and hydrates Level-2/3 on trigger.

### 6.4 Security & audit
- **FR-13** Every skill fetch is logged to `request_logs` (reuse the existing audit trail) with the API key, skill name, and level accessed.
- **FR-14** `allowed-tools` declarations are surfaced to admins and checked against farm policy before a skill is enabled.
- **FR-15** Bundled `scripts/` are scanned on upload; execution in the farm's own agent is sandboxed (§11.3).

---

## 7. Architecture overview

Skills slot into the existing farm topology as a **new content plane** behind the same ingress and auth.

```
                         ┌────────────────────────────────────────────────────────┐
                         │                 mcpfarm_internal (bridge)               │
  MCP client ─┐          │                                                        │
  (Cursor,    │  Bearer  │   ┌────────┐   forward_auth   ┌───────────────┐        │
   Claude) ───┼────────▶ │   │ Caddy  │ ───────────────▶ │ auth-gateway  │        │
              │          │   │  :80   │ ◀─────────────── │  :9090        │        │
  Filesystem ─┘          │   └───┬────┘   200 / 401      │  FastAPI      │        │
  agent (sync)               │        │                  │               │        │
                             │        │  proxy           │  ┌──────────┐ │        │
                             │        ├────────────────▶ │  │ skills   │ │        │
                             │        │                  │  │ store    │ │◀── /data/skills volume
                             │        │                  │  └──────────┘ │        │
                             │        │                  └──────┬────────┘        │
                             │        │                         │ SQLite (skills table)
                             │        ▼                         │                 │
                             │   ┌──────────────┐               │                 │
                             │   │  skills-mcp  │◀──────────────┘  (reads store)  │
                             │   │  (MCP server │                                  │
                             │   │   for skills)│   ── vector index (Redis) ──▶ doc_type:"skill"
                             │   └──────────────┘                                  │
                             └────────────────────────────────────────────────────┘
```

Three routes, one auth:
- `/{server}/mcp` → existing MCP servers (unchanged).
- `/skills-mcp/mcp` → the skills-as-MCP server (new container, but *farm-owned*, reads the store).
- `/skills/*` and `/admin/skills/*` → auth-gateway skill APIs (registry, catalog, bundles).

The **skills store** is a directory volume (`/data/skills`) owned by the auth-gateway; the DB holds metadata and pointers. This mirrors how servers are tracked in SQLite while their images live in Docker.

---

## 8. Skill package format & validation

### 8.1 On-disk layout in the store

```
/data/skills/
└── <skill-name>/
    └── <version>/                 # e.g. 1.0.0 or a content hash
        ├── SKILL.md
        ├── scripts/…
        ├── references/…
        ├── assets/…
        ├── .manifest.json         # farm-generated: file list + sizes + sha256
        └── .bundle.tar.gz         # farm-generated: reproducible archive for download
```

The `active` version per skill is recorded in the DB (`skills.active_version`). Uploading a new version never mutates an existing one (immutable versions → safe rollback).

### 8.2 Validation rules

**Hard errors (reject upload):**
- Missing `SKILL.md` or missing/empty `name` or `description`.
- `name` violates: not `^[a-z0-9]+(-[a-z0-9]+)*$`, or length > 64, or contains `--`, or contains `anthropic`/`claude`, or does not match the skill directory name.
- `description` > 1024 chars, or contains `<`/`>` (XML tags disallowed).
- `compatibility` > 500 chars (if present).
- Frontmatter is not valid YAML, or body is empty.
- Path traversal / absolute paths / symlinks in the archive; total size over a configurable cap; disallowed file types (see §16.3).

**Soft warnings (accept, surface to admin):**
- `SKILL.md` body > 500 lines (progressive-disclosure guidance).
- `description` missing an explicit "use when…" trigger clause.
- `allowed-tools` present (flag for policy review).
- References to bundled files that don't exist.

Validation is implemented in a new `skills_validator.py` and runs on every upload and on `reindex`. It returns a structured report reused by both the API and the UI.

---

## 9. Data model

New SQLite tables in the auth-gateway DB (`init_db()` in `main.py`). Column style mirrors the existing `servers` table.

```sql
CREATE TABLE IF NOT EXISTS skills (
    name            TEXT PRIMARY KEY,          -- kebab-case, == SKILL.md name
    display_name    TEXT,
    description     TEXT NOT NULL,             -- Level-1 routing signal
    category        TEXT,                      -- reuse category taxonomy
    active_version  TEXT NOT NULL,
    source          TEXT DEFAULT 'uploaded',   -- 'uploaded' | 'git' | 'builtin'
    source_url      TEXT,                      -- git remote, if any
    license         TEXT,
    compatibility   TEXT,
    allowed_tools   TEXT,                      -- raw frontmatter string, if present
    scopes          TEXT DEFAULT '*',          -- who may fetch (mirrors api_keys.scopes semantics)
    status          TEXT DEFAULT 'enabled',    -- 'enabled' | 'disabled'
    metadata        TEXT DEFAULT '{}',         -- JSON: author/version/etc from frontmatter
    body_lines      INTEGER DEFAULT 0,
    validation      TEXT DEFAULT '{}',         -- JSON: last validation report
    created_at      TEXT NOT NULL,
    updated_at      TEXT
);

CREATE TABLE IF NOT EXISTS skill_versions (
    skill_name      TEXT NOT NULL,
    version         TEXT NOT NULL,
    sha256          TEXT NOT NULL,             -- hash of .bundle.tar.gz
    size_bytes      INTEGER NOT NULL,
    file_count      INTEGER NOT NULL,
    created_at      TEXT NOT NULL,
    PRIMARY KEY (skill_name, version)
);
```

`request_logs` is reused for audit; the `server` column stores the skill name (prefixed, e.g. `skill:web-recon`) so existing `/admin/audit` queries work unchanged.

---

## 10. API surface

All admin routes require the `X-Admin-Secret` header (via `require_admin`); all public routes require a valid Bearer token (via `require_api_key` / Caddy `forward_auth`) — identical to the server APIs. Routes live in `main.py` next to the server endpoints.

### 10.1 Admin (management plane)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/admin/skills` | Upload a skill (`multipart/form-data` archive) **or** register from `{ "git_url": … }`. Returns the validation report + registered skill. |
| `GET` | `/admin/skills` | List all skills (incl. disabled) with full metadata + latest validation. |
| `GET` | `/admin/skills/{name}` | Skill detail + version history + file manifest. |
| `PATCH` | `/admin/skills/{name}` | Update `scopes`, `category`, `status`, `active_version`. |
| `DELETE` | `/admin/skills/{name}` | Remove skill (all versions) + purge vector docs. |
| `POST` | `/admin/skills/{name}/enable` \| `/disable` | Toggle availability across all delivery paths. |
| `POST` | `/admin/skills/{name}/validate` | Re-run validation against the active version. |
| `POST` | `/admin/skills/import` | Bulk import (array of archives or git URLs). |
| `POST` | `/admin/vectors/index-skill/{name}` | (Re)index a single skill into Redis. |

### 10.2 Public (data plane, Bearer-gated)

| Method | Path | Level | Description |
|--------|------|-------|-------------|
| `GET` | `/skills` | 1 | List enabled skills: `name`, `display_name`, `description`, `category`, `version`, `allowed_tools`. Cheap metadata only. |
| `GET` | `/skills/{name}` | 1–2 | Metadata + file manifest (no bodies). |
| `GET` | `/skills/{name}/SKILL.md` | 2 | The full `SKILL.md` (frontmatter + body). |
| `GET` | `/skills/{name}/files/{path}` | 3 | A single bundled resource (`scripts/…`, `references/…`, `assets/…`), path-validated. |
| `GET` | `/skills/{name}/bundle` | — | The reproducible `.tar.gz` for filesystem sync. |
| `GET` | `/skills/manifest.json` | 1 | Farm-wide manifest (all enabled skills + versions + hashes) for sync tooling. |

`GET /skills` deliberately returns **only** Level-1 fields so a client can cheaply enumerate everything, exactly like an agent pre-loading skill metadata.

### 10.3 Caddy routing (add to `caddy/Caddyfile`)

```caddyfile
# Skills registry + catalog (auth-gateway handles admin secret / bearer)
handle /admin/skills* {
    reverse_proxy auth-gateway:9090
}
handle /skills* {
    forward_auth auth-gateway:9090 {
        uri /verify
        copy_headers Authorization
    }
    reverse_proxy auth-gateway:9090
}
```

The `skills-mcp` container gets a normal dynamic route (`/skills-mcp/*`) generated exactly like every other MCP server, so it inherits `forward_auth`, scopes, rate limiting, and audit for free.

---

## 11. Delivery mechanisms (the crux)

Because skills have no single wire protocol, the farm offers three complementary delivery paths. All three read the **same** store and honor the **same** auth.

### 11.1 Path A — `skills-mcp` (skills as MCP resources) — *recommended default*

A small **farm-owned FastMCP server** (`skills-mcp`) that turns the skills store into MCP primitives, so **any MCP client** consumes skills through the exact path it already uses for tools — no client changes, no filesystem access needed.

- **Resources:** each skill exposes MCP resources:
  - `skill://<name>` → the `SKILL.md` body (Level 2).
  - `skill://<name>/files/<path>` → bundled resources (Level 3).
  - Resource **list** returns each skill's `name` + `description` (Level 1) as the resource description — mapping cleanly onto progressive disclosure.
- **Tools (for clients that prefer tools over resources):**
  - `list_skills(query?, category?)` → Level-1 metadata (optionally vector-ranked).
  - `get_skill(name)` → the body.
  - `get_skill_file(name, path)` → a resource file.
- **Auth/health/routing:** registered like any MCP server (`hackerdogs/skills-mcp`), reached at `/skills-mcp/mcp`, probed on `/mcp/`, indexed, scoped, audited — reusing all existing machinery in `main.py` and `docker_manager.py`.

This is the lowest-friction option and the one that makes skills "just appear" for MCP clients.

### 11.2 Path B — bundle sync (filesystem agents)

For runtimes that read `.claude/skills/` (Claude Code, Cursor, Claude Agent SDK), provide authenticated bundles plus a tiny sync helper.

- `GET /skills/manifest.json` lists every enabled skill with `name`, `version`, `sha256`, `bundle_url`.
- `GET /skills/{name}/bundle` streams the reproducible archive.
- A **`hd-skills` sync CLI** (thin shell/python script, shipped in `mcpfarm/scripts/`) does:
  1. Fetch the manifest with the Bearer token.
  2. Diff against locally installed versions (by hash).
  3. Download changed bundles and extract into `~/.claude/skills/<name>/` (or a project `.claude/skills/`).
  4. Optionally drop a matching `mcp.json` (from the existing `/admin/servers/mcp-config`) so referenced farm tools are wired up too.

This preserves progressive disclosure because the runtime itself only loads metadata until a skill triggers.

### 11.3 Path C — native farm chat (server-side progressive disclosure)

The farm's own Chat page (`chat_proxy.py` + the React chat UI) applies skills directly:

1. **Level 1 (always):** on each chat turn, inject a compact **skills index** into the system prompt — one line per enabled, in-scope skill: `- <name>: <description>`. (Budgeted; if the catalog is large, pre-filter with a vector search over `doc_type:"skill"` on the user's message.)
2. **Level 2 (on trigger):** expose an internal `load_skill(name)` tool (or detect an explicit skill mention). When the model calls it, the proxy fetches `SKILL.md` from the store and appends the body as a system/context message for subsequent turns.
3. **Level 3 (on demand):** expose `read_skill_file(name, path)` and, for executable steps, `run_skill_script(name, path, args)` — **sandboxed** (see below).

**Sandboxing for Path C script execution:**
- Scripts run in an **ephemeral, network-restricted container** (a dedicated `skills-runner` image), never on the auth-gateway host.
- Read-only mount of that skill version's `scripts/`, a scratch `/tmp`, CPU/mem/time limits, no Docker socket, dropped capabilities.
- Output is captured and returned to the loop like any tool result.
- This is the **only** place the farm executes skill code, and it is opt-in per deployment (`SKILLS_ALLOW_EXEC=1`).

> Path C is powerful but is the highest-risk path; ship A and B first (§16), gate C behind explicit config, and route every `run_skill_script` through the L3 tool-call firewall.

### 11.4 Choosing a path

| Client | Recommended path |
|--------|------------------|
| Cursor / Claude Desktop / generic MCP client | **A** (`skills-mcp`) |
| Claude Code / Claude Agent SDK / CI agents | **B** (bundle sync into `.claude/skills/`) |
| Farm's built-in Chat | **C** (native progressive disclosure) |

---

## 12. Vector index integration

Skills join the existing Redis vector pipeline (`vector_index.py`, `vector_indexer.py`) so semantic search and the chat assistant find them alongside servers and tools.

- Add `doc_type: "skill"` (and optionally `skill-ref` for body chunks) to the indexer.
- **Documents per skill:**
  - `skill:<name>:meta` → embed `display_name + name + category + description` (the Level-1 routing signal). `text` = description.
  - `skill:<name>:body:<idx>` → chunk the `SKILL.md` body with the existing `chunk_readme()` splitter; `doc_type: "skill-body"`.
- Reuse `build_server_docs`-style construction in a new `build_skill_docs()`; reuse `_embed_and_upsert`, `delete_*_docs`, and `set_*_status`.
- `/vectors/search` gains skills automatically once they're indexed; the two-stage server→tool search grows a parallel skill lane, or skills are merged into stage-1 discovery results with a `type` field so the chat can decide whether the best answer is a *tool* or a *skill*.
- Index lifecycle mirrors servers: index on enable/upload, drop on disable/delete (best-effort helpers like `_vector_index_server_safe`).

---

## 13. UI — Skills tab

Add a **Skills** entry to the top nav in `mcpfarm-ui/src/App.jsx` (`MODES`), reusing Marketplace patterns:

- **`SkillsMarketplace.jsx`** — searchable, category-filtered grid of skill cards (name, description, category, version, `allowed-tools` badge, enabled toggle). Mirrors `Marketplace.jsx`.
- **`SkillDetail.jsx`** — renders `SKILL.md` via the existing `MarkdownViewer.jsx`; shows the file manifest (`scripts/`/`references/`/`assets/`), validation report, version history, and copy-paste install snippets for each delivery path (MCP config for `skills-mcp`, the `hd-skills sync` command, and "use in Chat").
- **`AddSkillDialog.jsx`** — drag-drop a `.zip`/`.tar.gz` or paste a Git URL; shows the live validation report before commit. Mirrors `AddServerDialog.jsx`.
- **Chat integration:** a "Skills" affordance in the composer (like `ComposerToolsButton.jsx`) to pin/enable specific skills for a conversation.
- **API client:** extend `mcpfarm-ui/src/lib/api.js` with `listSkills`, `getSkill`, `uploadSkill`, `setSkillStatus`, etc.

---

## 14. Composition with MCP servers

- A skill body may name farm servers (e.g. "use `naabu-mcp`, then `httpx-mcp`"). The detail page and bundle can attach a **scoped `mcp.json`** generated by the existing `/admin/servers/mcp-config` endpoint, so installing a skill can also wire up the tools it needs.
- `skills-mcp` can advertise, in `get_skill`, the list of referenced servers and whether they're currently enabled/healthy (join against the `servers` table), giving the agent an actionable "these tools are available" hint.
- Optional frontmatter convention (in `metadata`): `mcp_servers: naabu-mcp, httpx-mcp` to make the dependency explicit and machine-checkable at enable time.

---

## 15. Configuration & deployment

New env vars (document in `mcpfarm/.env.example` and `DEPLOY.md`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SKILLS_ROOT` | `/data/skills` | Store root (mounted volume). |
| `SKILLS_MAX_BUNDLE_MB` | `25` | Upload size cap. |
| `SKILLS_ALLOW_EXEC` | `0` | Enable Path C `run_skill_script` (sandboxed). |
| `SKILLS_RUNNER_IMAGE` | `hackerdogs/skills-runner:latest` | Sandbox image for script execution. |
| `SKILLS_ALLOWED_FILE_TYPES` | `md,txt,py,sh,js,json,yaml,yml,csv,png,svg,jinja,j2` | Allowlist for bundled files. |

Compose changes:
- Add the `skills` volume (mounted by auth-gateway and `skills-mcp`).
- Add the `skills-mcp` service (built like other MCP servers) and register it in `port-map.json`.
- Add the `skills-runner` image (built, not run persistently) for Path C.
- `deploy.sh seed` also seeds any **builtin** skills shipped in the repo (e.g. `mcpfarm/skills/*`).

---

## 16. Rollout plan (phased)

| Phase | Deliverables | Risk |
|-------|-------------|------|
| **P0 — Registry** | DB tables, `skills_validator.py`, admin CRUD, store on `/data/skills`, versioning, audit. | Low |
| **P1 — Discovery** | Public `/skills*` endpoints, Caddy routes, vector indexing (`doc_type:"skill"`), UI Skills tab (list/detail/upload). | Low |
| **P2 — Path A** | `skills-mcp` FastMCP server (resources + `list_skills`/`get_skill` tools), registered like any server. | Medium |
| **P3 — Path B** | `manifest.json`, bundle download, `hd-skills` sync CLI, optional `mcp.json` attach. | Medium |
| **P4 — Path C** | Native chat progressive disclosure; `load_skill`/`read_skill_file`; **sandboxed** `run_skill_script` behind `SKILLS_ALLOW_EXEC`, routed through L3 firewall. | High |
| **P5 — Authoring** | In-UI skill editor, lint-on-save, git-backed versioning, signing. | Medium |

Security GA = P0–P3 (no host-side execution). P4 requires the sandbox and L3 firewall.

---

## 17. Security model

Skills add content risk (prompt-injection via instructions), supply-chain risk (bundled code), and capability risk (`allowed-tools`). Controls:

- **Auth parity:** every skill fetch passes Caddy `forward_auth` → Bearer token → scopes → rate limit → audit, identical to MCP.
- **Immutable versions + hashing:** each version is content-addressed (`sha256`); bundles are reproducible; rollback is trivial; clients verify hashes on sync.
- **Upload scanning:** validate schema (§8.2); block path traversal/symlinks/oversized/disallowed types; run **`trufflehog`/`gitleaks`** (already in the catalog) over the bundle for secrets, and optionally **`semgrep`** over `scripts/`.
- **`allowed-tools` governance:** parsed and shown to admins; a skill declaring tools is `disabled` by default until an admin approves; the declaration is advisory to external runtimes but **enforced** for Path C via the sandbox + L3 policy.
- **Execution isolation (Path C only):** ephemeral, network-restricted, capability-dropped `skills-runner` container; no Docker socket; CPU/mem/time caps; read-only script mount; every invocation logged and firewall-checked.
- **Prompt-injection awareness:** skill bodies are untrusted content; when injected into the farm chat system prompt they are clearly delimited and the L1/L2 companion guards (InferShield/LlamaFirewall, per the gateway roadmap) still apply to model output.
- **DLP:** redact secrets from audit logs; never store upstream API keys in skills.

---

## 18. Success criteria

| Criterion | Target |
|-----------|--------|
| Upload → validated & registered | < 5 s for a typical skill bundle |
| `GET /skills` (Level-1 catalog) latency | < 50 ms for 500 skills |
| MCP client sees farm skills (Path A) | Zero client config beyond adding `skills-mcp` |
| Filesystem sync (Path B) | Idempotent; only changed skills re-downloaded (hash diff) |
| Progressive disclosure preserved | Metadata-only until trigger on all three paths |
| Discovery | A skill is findable via `/vectors/search` and chat within one reindex cycle |
| Disable propagation | Disabled skill vanishes from all paths + vector index immediately |
| Isolation (Path C) | No skill script can reach the Docker socket, the DB, or the network by default |

---

## 19. Open questions

1. **Resource vs tool for Path A:** expose skills primarily as MCP **resources**, **tools**, or both? (Resources map cleanest to progressive disclosure, but tool support is more universally implemented across clients.)
2. **Versioning scheme:** semver from frontmatter `metadata.version` vs content-hash vs both? What's the pin/rollback UX?
3. **Scopes granularity:** reuse the comma-separated server-scope model, or introduce skill-specific groups/tags?
4. **Builtin skills:** ship a curated set (e.g. `web-recon`, `cloud-audit`, `report-writer`) in-repo under `mcpfarm/skills/`? Which ones?
5. **Trust namespace:** restrict uploads to a `hackerdogs/*` author namespace, mirror the "only Hackerdogs images" server policy, or allow arbitrary authored skills with scanning only?
6. **Cross-instance sync (P5):** how do skills replicate across multi-instance farms (see gateway spec §14–§16)?
7. **`allowed-tools` enforcement:** for external runtimes the farm can only *advise*; is that acceptable, or do we require Path A/C for capability-sensitive skills?

---

## 20. FAQ

Grouped from **basic → intermediate → advanced**, then an **execution deep-dive** (where scripts run) and the **recommended path**.

### 20.1 Basics — "what is a skill?"

**Q1. In one sentence, what is a Claude Skill?**
A skill is a **folder of instructions** — a `SKILL.md` file (YAML frontmatter + Markdown) plus optional `scripts/`, `references/`, and `assets/` — that teaches an agent *how* to do a task and *when* to do it. It is content, not a running service.

**Q2. How is a skill different from an MCP server/tool?**
An **MCP server** is a running container that *executes* functions (a port scan, a hash lookup) and returns data. A **skill** is *knowledge*: a procedure the agent reads and follows. A tool is a verb the agent can call; a skill is a playbook that may tell the agent which verbs to call and in what order. See §3 for the full comparison. Crucially, a skill often *orchestrates* farm MCP tools ("use `naabu-mcp`, then `httpx-mcp`, then summarize").

**Q3. What is inside a skill package?**
```
skill-name/
├── SKILL.md         # required: name + description (metadata) + Markdown instructions
├── scripts/         # optional: executable helpers (python/bash/js)
├── references/      # optional: docs the agent reads on demand
└── assets/          # optional: templates/icons used in output
```
Only `SKILL.md` is required. The `name` and `description` fields are mandatory; everything else is optional (§2.2).

**Q4. Why does the `description` matter so much?**
It is the **routing signal**. An agent loads *only* every skill's `name` + `description` at startup (~100 tokens each) and matches your request against those descriptions to decide which skill to open. A vague description means the skill never triggers. It must state **both** what the skill does **and** when to use it.

**Q5. What is "progressive disclosure"?**
The three-level loading model that keeps skills cheap until relevant:
1. **Metadata** (`name`+`description`) — always loaded.
2. **Body** (`SKILL.md` content) — loaded only when the skill triggers.
3. **Resources** (`scripts/`, `references/`, `assets/`) — loaded/executed only when explicitly needed.
The farm preserves this on every delivery path (§2.3, §11).

**Q6. Does adding lots of skills bloat the context window?**
No. Until a skill triggers, it costs only its ~100-token metadata line. That's the whole point of progressive disclosure — you can host hundreds of skills with negligible idle cost.

**Q7. Do I need to be a developer to use a skill?**
No. A user just "installs" a skill (adds `skills-mcp` to their client, runs the sync command, or enables it in the farm Chat). The plumbing is invisible — same philosophy as the rest of the farm.

### 20.2 Intermediate — using skills with the farm

**Q8. How does the farm store skills?**
As immutable, versioned folders under the `/data/skills` volume, with metadata + pointers in a SQLite `skills` table. Each version is content-hashed (`sha256`) so rollbacks and client-side integrity checks are trivial (§8, §9).

**Q9. How do I get a farm skill into my client?**
Three paths, all behind the same Bearer-token auth (§11):
- **Path A — `skills-mcp`:** add one MCP server to your client; skills appear as MCP resources/tools. No filesystem access needed.
- **Path B — bundle sync:** run the `hd-skills` CLI to download approved skills into `~/.claude/skills/` (or a project `.claude/skills/`).
- **Path C — farm Chat:** skills are applied automatically inside the farm's own chat.

**Q10. Are skills discoverable like servers?**
Yes. They're indexed into the same Redis vector store as `doc_type:"skill"`, so `/vectors/search` and the chat assistant surface skills next to servers and tools (§12).

**Q11. How is a skill secured/authenticated?**
Identically to MCP servers: every fetch passes Caddy `forward_auth` → Bearer token → scopes → rate limit → audit log. Per-skill `scopes` restrict who can fetch which skill (§17).

**Q12. Can I disable a skill instantly?**
Yes. `POST /admin/skills/{name}/disable` removes it from **all** delivery paths and the vector index immediately (FR-4).

**Q13. How do skills and MCP servers work together?**
A skill body can name farm servers, and the farm can attach a scoped `mcp.json` (from the existing `/admin/servers/mcp-config`) to a bundle so installing a skill also wires up the tools it needs. `skills-mcp` can report whether referenced servers are currently enabled/healthy (§14).

**Q14. What happens if a skill references a tool/server I don't have?**
The skill still installs, but the agent may be unable to complete steps that need the missing server. The detail page lists a skill's `mcp_servers` dependency (optional frontmatter `metadata`), and `skills-mcp` flags unavailable ones so the gap is visible up front.

### 20.3 Advanced — authoring, validation, versioning

**Q15. What makes a skill upload get rejected?**
Hard errors: missing `SKILL.md`/`name`/`description`; `name` not kebab-case / >64 chars / contains `--` / contains `anthropic`/`claude` / doesn't match the folder; `description` >1024 chars or containing XML tags; invalid YAML; path traversal, symlinks, oversized archive, or disallowed file types. Soft warnings (accepted, surfaced): body >500 lines, missing "use when…" trigger, `allowed-tools` present (§8.2).

**Q16. What is `allowed-tools` and does the farm enforce it?**
`allowed-tools` is optional frontmatter declaring pre-approved tools (e.g. `Bash(git:*) Read`). It's honored by Claude Code CLI but **not** by the Agent SDK. In the farm it is **advisory** for external runtimes (Paths A/B) — the farm surfaces it to admins and auto-disables such skills pending approval — but **enforced** for the farm's own execution path (Path C) via the sandbox + L3 firewall (§17).

**Q17. How does versioning work?**
Uploads never mutate an existing version; each new upload is a new immutable, hashed version. `skills.active_version` points at the live one, so rollback = flip the pointer. Clients sync by hash diff, downloading only what changed (§8.1, §11.2).

**Q18. Can skills contain secrets/malware? What stops that?**
On upload the farm validates the schema and runs supply-chain scans — `trufflehog`/`gitleaks` for secrets over the whole bundle and optionally `semgrep` over `scripts/` (all already in the farm catalog). Skills that declare tools are disabled by default until an admin approves. Skill bodies are treated as untrusted content when injected into the farm chat (§17).

**Q19. Can I author/edit skills inside the farm UI?**
Not in v1 (upload/import + view only). An in-browser editor with lint-on-save and git-backed versioning is planned for P5 (§4.2, §16).

### 20.4 Execution deep-dive — "where do the scripts run?"

This is the most important architectural question, so it gets its own section.

**Q20. A skill can bundle `scripts/`. Where do those scripts actually run?**
**It depends on the delivery path — and by default the farm does *not* run your scripts.**

| Delivery path | Who executes `scripts/` | Where it runs |
|---------------|-------------------------|---------------|
| **A — `skills-mcp`** | The **client's** agent runtime | On the **client** (the farm only *serves* the files; it never executes them) |
| **B — bundle sync** | The **client's** agent runtime (Claude Code/Cursor/SDK) | On the **client machine**, per that runtime's own rules |
| **C — farm Chat** | The **farm** | In an **isolated, ephemeral Docker container** on the farm (`skills-runner`), and **only** if `SKILLS_ALLOW_EXEC=1` |

So: for Paths A and B, scripts are downloaded to (or read by) the client and run **on the client** under the client agent's sandbox/permissions — the farm is purely a distribution point. For Path C, when a user runs a skill inside the farm's *own* chat agent, the farm executes the script itself, but always inside a locked-down throwaway container — never on the auth-gateway host.

**Q21. So does the farm run scripts in an isolated Docker container, or does the client download them?**
**Both models exist, deliberately:**
- **Client-side execution (default for external clients, Paths A & B):** the script travels to the client and runs there. The farm assumes no execution responsibility; the consuming agent (Claude Code, Cursor, the SDK) applies its own tool permissions and sandbox.
- **Farm-side isolated execution (Path C only, opt-in):** the farm spins up a dedicated `skills-runner` container to execute the script, then destroys it. This is the *only* place the farm runs skill code, and it is off unless the operator sets `SKILLS_ALLOW_EXEC=1`.

**Q22. What exactly does the Path-C sandbox (`skills-runner`) look like?**
An ephemeral container with, at minimum (§11.3, §17):
- **Network restricted** (no egress by default; allowlist only if a skill legitimately needs it).
- **No Docker socket**, dropped Linux capabilities, non-root user.
- **Read-only mount** of that skill version's `scripts/` only; a writable scratch `/tmp`.
- **CPU / memory / wall-clock limits**; the container is killed and removed after the run.
- Every invocation is **audit-logged** and routed through the **L3 tool-call firewall** before it runs.

**Q23. Why not just always run scripts on the farm?**
Two reasons. First, **trust**: running arbitrary uploaded code on shared farm infrastructure is the highest-risk operation in the whole design, so it's isolated and opt-in. Second, **semantics**: skills are a client-runtime concept — Claude Code and the SDK already know how to discover and run skills from `.claude/skills/`, so for those clients the correct, least-surprising behavior is to deliver the files and let the client run them.

**Q24. If scripts run on the client, does the farm lose control/visibility?**
For Paths A/B the farm controls **distribution and governance** (what exists, who can fetch it, what version, integrity hashes, scanning, enable/disable, audit of *fetches*) but not the *execution* — that's the client's runtime. If you need the farm to enforce execution policy end-to-end, use **Path C**, where the farm both serves and runs the code under its own sandbox and firewall.

**Q25. Can a skill's script reach the farm database, Docker socket, or network?**
No (Path C). The sandbox has no Docker socket, no DB credentials, and no network egress by default. Even the script files are mounted read-only. That isolation is the precondition for enabling `SKILLS_ALLOW_EXEC` at all.

**Q26. What if a skill has no scripts — just instructions?**
Then there's nothing to execute anywhere; the agent simply reads the Markdown body and acts (often by calling farm MCP tools). Many high-value skills are pure instructions + a reference template.

### 20.5 Recommended path

**Q27. Which delivery path should I use?**

| Your situation | Use | Why |
|----------------|-----|-----|
| Cursor, Claude Desktop, or any generic MCP client | **Path A — `skills-mcp`** | Zero client changes beyond adding one MCP server; skills appear as resources/tools; nothing executes on your machine unless *you* act on the instructions. |
| Claude Code, Claude Agent SDK, CI/automation agents | **Path B — bundle sync** | These runtimes natively read `.claude/skills/`; sync gives them the real files (and an optional matching `mcp.json`) so their built-in Skill tooling works. |
| Users of the farm's own Chat page | **Path C — native chat** | The farm applies skills automatically with server-side progressive disclosure; only path that can *enforce* execution policy end-to-end. |

**Q28. What is the single recommended default?**
**Path A (`skills-mcp`).** It's the lowest-friction, most universal, and safest-by-default option: any MCP client gets skills through the path it already trusts, the farm never executes anything, and all access is governed by the existing zero-trust auth. Layer in **Path B** for filesystem-native agents that want the real `.claude/skills/` files, and enable **Path C** only when you specifically want the farm itself to run skill scripts under its sandbox.

**Q29. What's the recommended rollout order for operators?**
Ship **P0–P3** first (registry → discovery → Path A → Path B) — none of these execute code on the farm, so they're security-GA. Enable **Path C (P4)** later, deliberately, behind `SKILLS_ALLOW_EXEC=1` with the `skills-runner` sandbox and L3 firewall in place (§16).

---

## Appendix A — Example `SKILL.md` (farm-native, composes MCP servers)

```markdown
---
name: web-recon
description: Run a structured external web reconnaissance workflow against an authorized domain and produce a findings summary. Use when the user asks to enumerate subdomains, fingerprint web tech, or map the attack surface of a website they are authorized to test.
license: Apache-2.0
compatibility: Requires the naabu-mcp, httpx-mcp, and subfinder-mcp farm servers.
metadata:
  author: hackerdogs
  version: "1.0.0"
  mcp_servers: "subfinder-mcp, httpx-mcp, naabu-mcp"
---

# Web Recon Workflow

## When to use
Use for authorized external recon only. Confirm the target is in scope before starting.

## Steps
1. Enumerate subdomains with `subfinder-mcp`.
2. Probe live hosts and fingerprint tech with `httpx-mcp`.
3. Port-scan live hosts with `naabu-mcp` (top 1000 ports).
4. Summarize findings grouped by host; flag anything unusual.

## Output
A Markdown report: hosts, open ports, detected technologies, and recommended next steps.
See `references/report-template.md` for the exact format.
```

## Appendix B — Example API payloads

**Register from Git:**
```bash
curl -X POST http://localhost:8485/admin/skills \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"git_url": "https://github.com/hackerdogs/skill-web-recon", "category": "network-recon"}'
```

**Upload a bundle:**
```bash
curl -X POST http://localhost:8485/admin/skills \
  -H "X-Admin-Secret: $ADMIN_SECRET" \
  -F "file=@web-recon.zip" -F "category=network-recon"
```

**Level-1 catalog (Bearer-gated):**
```bash
curl http://localhost:8485/skills -H "Authorization: Bearer hd_sk_..."
```
```json
{
  "skills": [
    {
      "name": "web-recon",
      "display_name": "Web Recon",
      "description": "Run a structured external web reconnaissance workflow...",
      "category": "network-recon",
      "version": "1.0.0",
      "allowed_tools": null
    }
  ],
  "count": 1
}
```

**Fetch the body (Level 2):**
```bash
curl http://localhost:8485/skills/web-recon/SKILL.md -H "Authorization: Bearer hd_sk_..."
```

## Appendix C — `skills-mcp` MCP surface (sketch)

```jsonc
// tools/list
[
  { "name": "list_skills",
    "description": "List available farm skills (name + description). Optionally filter by query/category.",
    "inputSchema": { "type": "object", "properties": {
      "query": {"type": "string"}, "category": {"type": "string"} } } },
  { "name": "get_skill",
    "description": "Fetch the full SKILL.md body for a skill by name.",
    "inputSchema": { "type": "object", "properties": {
      "name": {"type": "string"} }, "required": ["name"] } },
  { "name": "get_skill_file",
    "description": "Fetch a bundled resource file (scripts/references/assets) from a skill.",
    "inputSchema": { "type": "object", "properties": {
      "name": {"type": "string"}, "path": {"type": "string"} },
      "required": ["name", "path"] } }
]

// resources/list  (progressive disclosure: description == Level-1 metadata)
[
  { "uri": "skill://web-recon", "name": "web-recon",
    "description": "Run a structured external web reconnaissance workflow...",
    "mimeType": "text/markdown" }
]
```

## Appendix D — Farm manifest (Path B sync)

```jsonc
// GET /skills/manifest.json
{
  "generated_at": "2026-07-24T13:47:00Z",
  "skills": [
    {
      "name": "web-recon",
      "version": "1.0.0",
      "sha256": "b1946ac9…",
      "size_bytes": 20480,
      "bundle_url": "/skills/web-recon/bundle"
    }
  ]
}
```

## Appendix E — Files touched (implementation map)

| Area | File(s) | Change |
|------|---------|--------|
| DB & API | `mcpfarm/auth-gateway/main.py` | `init_db()` tables; `/admin/skills*` + `/skills*` routes; audit reuse. |
| Models | `mcpfarm/auth-gateway/models.py` | `Skill`, `SkillVersion`, request/response schemas. |
| Validation | `mcpfarm/auth-gateway/skills_validator.py` *(new)* | Spec validation + bundle safety checks. |
| Store | `mcpfarm/auth-gateway/skills_store.py` *(new)* | Filesystem store, versioning, bundling, manifest. |
| Vectors | `mcpfarm/auth-gateway/vector_indexer.py`, `vector_index.py` | `build_skill_docs()`, `doc_type:"skill"`, index/drop helpers. |
| Chat | `mcpfarm/auth-gateway/chat_proxy.py` | Level-1 skills index injection; `load_skill`/`read_skill_file`/`run_skill_script` tools (Path C). |
| MCP delivery | `skills-mcp/` *(new server)*, `mcpfarm/port-map.json` | FastMCP server exposing skills as resources/tools. |
| Sandbox | `skills-runner/` *(new image)* | Ephemeral, isolated script executor for Path C. |
| Ingress | `mcpfarm/caddy/Caddyfile` | `/admin/skills*` + `/skills*` handlers. |
| Deploy | `mcpfarm/docker-compose.yml`, `deploy.sh`, `.env.example`, `DEPLOY.md` | `skills` volume, `skills-mcp` service, env vars, seed builtin skills. |
| UI | `mcpfarm-ui/src/App.jsx`, `components/SkillsMarketplace.jsx`, `SkillDetail.jsx`, `AddSkillDialog.jsx`, `lib/api.js` | Skills tab, list/detail/upload, chat pinning. |
```
