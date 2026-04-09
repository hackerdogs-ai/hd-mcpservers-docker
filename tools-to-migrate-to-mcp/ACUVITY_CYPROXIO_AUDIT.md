# Acuvity / Cyproxio MCP Servers — Intersection Audit

Sources:
- **Cyproxio:** `tools-to-migrate-to-mcp/cyproxio/mcp-for-security-main` (original MCP servers; TypeScript, stdio only)
- **Acuvity:** `tools-to-migrate-to-mcp/acuvity/mcp-servers-registry-main` (wrappers over Cyproxio + others; Docker/Helm, Minibridge for HTTP/SSE)
- **Minibridge (local copy):** `tools-to-migrate-to-mcp/acuvity/minibridge-main` — Acuvity’s Go bridge (see §6)
- **Hackerdogs:** repo root `*-mcp/` (our built servers; FastMCP, stdio + streamable-http)

---

## 1. Summary

| Question | Answer |
|----------|--------|
| **Cyproxio MCP servers (total)** | 23 (from mcp-for-security-main) |
| **Layered by Acuvity** | 19 (Acuvity image + card points to cyproxio/mcp-for-security) |
| **Already Hackerdogs-built** | 5 (commix, scoutsuite, sslscan, smuggler, wpscan) |
| **HTTP streamable in Cyproxio source** | No — stdio only (`StdioServerTransport`) |
| **HTTP streamable in Acuvity image** | Yes — HTTP/SSE via Minibridge (port 8000, `/sse`) |

---

## 2. Migration status (all 23)

| # | Cyproxio tool | Root folder | Port | Status |
|---|---------------|-------------|------|--------|
| 1 | alterx | **alterx-mcp** | 8380 | ✅ Migrated |
| 2 | amass | **amass-mcp** | 8382 | ✅ Migrated |
| 3 | arjun | **arjun-mcp** | 8383 | ✅ Migrated |
| 4 | assetfinder | **assetfinder-mcp** | 8384 | ✅ Migrated |
| 5 | cero | **cero-mcp** | 8396 | ✅ Migrated |
| 6 | commix | **commix-mcp** | 8225 | ✅ Verified |
| 7 | crtsh | **crtsh-mcp** | 8381 | ✅ Migrated |
| 8 | ffuf | **ffuf-mcp** | 8385 | ✅ Migrated |
| 9 | gowitness | **gowitness-mcp** | 8397 | ✅ Migrated |
| 10 | http-headers-security | **http-headers-security-mcp** | 8392 | ✅ Migrated (install TBD) |
| 11 | httpx | **httpx-mcp** | 8386 | ✅ Migrated |
| 12 | katana | **katana-mcp** | 8387 | ✅ Migrated |
| 13 | masscan | **masscan-mcp** | 8388 | ✅ Migrated |
| 14 | mobsf | **mobsf-mcp** | 8389 | ✅ Migrated (install TBD) |
| 15 | nmap | **nmap-mcp** | 8390 | ✅ Migrated |
| 16 | nuclei | **nuclei-mcp** | 8391 | ✅ Migrated |
| 17 | scoutsuite | **scoutsuite-mcp** | 8251 | ✅ Verified |
| 18 | shuffledns | **shuffledns-mcp** | 8393 | ✅ Migrated |
| 19 | smuggler | **smuggler-mcp** | 8291 | ✅ Verified |
| 20 | sqlmap | **sqlmap-mcp** | 8394 | ✅ Migrated |
| 21 | sslscan | **sslscan-mcp** | 8323 | ✅ Verified |
| 22 | waybackurls | **waybackurls-mcp** | 8395 | ✅ Migrated |
| 23 | wpscan | **wpscan-mcp** | 8220 | ✅ Verified |

All 23 have a root folder; stdio + streamable-http via FastMCP; no Minibridge.

---

## 2.1 Final status (23 servers)

**Image built:** ✅ = `docker build` succeeded and image exists. **—** = image missing (build not run, or build failed). **Test:** ✅ = `test.sh` passed; **—** = not run (no image).

| # | Tool | Root folder | Port | Migrated | Image built | Test (compliance) |
|---|------|-------------|------|----------|-------------|-------------------|
| 1 | alterx | **alterx-mcp** | 8380 | ✅ | ✅ | ✅ |
| 2 | amass | **amass-mcp** | 8382 | ✅ | ✅ | ✅ |
| 3 | arjun | **arjun-mcp** | 8383 | ✅ | ✅ | ✅ |
| 4 | assetfinder | **assetfinder-mcp** | 8384 | ✅ | ✅ | ✅ |
| 5 | cero | **cero-mcp** | 8396 | ✅ | ✅ | ✅ |
| 6 | commix | **commix-mcp** | 8225 | ✅ | ✅ | ✅ |
| 7 | crtsh | **crtsh-mcp** | 8381 | ✅ | ✅ | ✅ |
| 8 | ffuf | **ffuf-mcp** | 8385 | ✅ | ✅ | ✅ |
| 9 | gowitness | **gowitness-mcp** | 8397 | ✅ | ✅ | ✅ |
| 10 | http-headers-security | **http-headers-security-mcp** | 8392 | ✅ (install TBD) | ✅ | ✅ |
| 11 | httpx | **httpx-mcp** | 8386 | ✅ | ✅ | ✅ |
| 12 | katana | **katana-mcp** | 8387 | ✅ | ✅ | ✅ |
| 13 | masscan | **masscan-mcp** | 8388 | ✅ | ✅ | ✅ |
| 14 | mobsf | **mobsf-mcp** | 8389 | ✅ (install TBD) | ✅ | ✅ |
| 15 | nmap | **nmap-mcp** | 8390 | ✅ | ✅ | ✅ |
| 16 | nuclei | **nuclei-mcp** | 8391 | ✅ | ✅ | ✅ |
| 17 | scoutsuite | **scoutsuite-mcp** | 8251 | ✅ | ✅ | ✅ |
| 18 | shuffledns | **shuffledns-mcp** | 8393 | ✅ | ✅ | ✅ |
| 19 | smuggler | **smuggler-mcp** | 8291 | ✅ | ✅ | ✅ |
| 20 | sqlmap | **sqlmap-mcp** | 8394 | ✅ | ✅ | ✅ |
| 21 | sslscan | **sslscan-mcp** | 8323 | ✅ | ✅ | ✅ |
| 22 | waybackurls | **waybackurls-mcp** | 8395 | ✅ | ✅ | ✅ |
| 23 | wpscan | **wpscan-mcp** | 8220 | ✅ | ✅ | ✅ |

**Summary:** 23/23 migrated. **Image built** = `docker build` ran and succeeded (image exists). **Test** = `./test.sh` passed (compliance: image exists, stdio tools/list+call, HTTP streamable tools/list+call). **—** = not done. All 23: image built and test.sh passed where applicable. Build any missing image with `docker build -t hackerdogs/<folder>:latest <folder>/` (e.g. waybackurls-mcp); test with `./test.sh` in that folder.

---

## 2.2 Gowitness: original Cyproxio vs Hackerdogs (migration plan)

**Source:** `tools-to-migrate-to-mcp/cyproxio/mcp-for-security-main/gowitness-mcp/`

**What the original does:**
- **Stack:** Node/TypeScript, MCP SDK, **stdio only** (`StdioServerTransport`). Invoked as `node build/index.js <gowitness_binary_path>`.
- **Five MCP tools:**
  1. **gowitness-screenshot** — Single URL: `gowitness scan single --url <url>`. Options: chrome window size, screenshot_path, timeout, delay, fullpage, format (jpeg/png), threads, write_db, write_jsonl, user_agent. Can return screenshot as base64 or save to directory.
  2. **gowitness-report** — `gowitness report` with screenshot_path, db_uri, output_format (html/csv/json).
  3. **gowitness-batch-screenshot** — Writes URLs to a file, runs `gowitness scan file -f <file>` with screenshot_path and options.
  4. **gowitness-read-binary** — Read a screenshot file from disk, return binary + metadata.
  5. **gowitness-list-screenshots** — List screenshot files in a directory with metadata.
- **Dependencies:** gowitness binary (Go 1.25+); no Chrome in the Node app (gowitness brings its own Chrome/headless usage).

**Hackerdogs migration (root `gowitness-mcp/`):**
- FastMCP, stdio + **streamable-http** (MCP_PORT 8397). Single tool **run_gowitness(arguments)**. Docker image: **Go 1.25** builder; runtime includes **Chromium** (symlinked as google-chrome) and **dumb-init** for screenshot capability and to avoid Chrome zombies.
- **Compliance:** `./test.sh` run in `gowitness-mcp/` — **5/5 passed** (1=image exists, 2=stdio tools/list, 3=stdio tools/call, 4=HTTP streamable tools/list, 5=HTTP streamable tools/call). Test assumes image already built; build first with `docker build -t hackerdogs/gowitness-mcp:latest .` if needed.

---

## 3. Detailed Table

| # | Cyproxio tool | In Acuvity registry? | Acuvity image name | Already Hackerdogs-built? | HTTP streamable (Cyproxio source) | HTTP streamable (Acuvity image) | Action to fix |
|---|---------------|----------------------|--------------------|---------------------------|------------------------------------|----------------------------------|----------------|
| 1 | alterx | Yes | mcp-server-alterx | No (we have acuvity-mcp-server-alterx-mcp as config-only) | No (stdio only) | Yes (Minibridge /sse, port 8000) | Add Dockerfile + test.sh for alterx; or align acuvity config with §2 |
| 2 | amass | Yes | mcp-server-amass | No | No | Yes | Same |
| 3 | arjun | Yes | mcp-server-arjun | No | No | Yes | Same |
| 4 | assetfinder | Yes | mcp-server-assetfinder | No | No | Yes | Same |
| 5 | cero | No | — | No | No | — | Build from cyproxio only |
| 6 | commix | No | — | **Yes** (commix-mcp) | No | — | Verify commix-mcp has streamable-http + test |
| 7 | crtsh | Yes | mcp-server-crtsh | No | No | Yes | Add/copy config or build from cyproxio |
| 8 | ffuf | Yes | mcp-server-ffuf | No | No | Yes | Same |
| 9 | gowitness | No | — | No | No | — | Build from cyproxio only |
| 10 | http-headers-security | Yes (as oshp) | mcp-server-oshp | No | No | Yes | Same |
| 11 | httpx | Yes | mcp-server-httpx | No | No | Yes | Same |
| 12 | katana | Yes | mcp-server-katana | No | No | Yes | Same |
| 13 | masscan | Yes | mcp-server-masscan | No | No | Yes | Same |
| 14 | mobsf | Yes | mcp-server-mobsf | No | No | Yes | Same |
| 15 | nmap | Yes | mcp-server-nmap | No | No | Yes | Same |
| 16 | nuclei | Yes | mcp-server-nuclei | No | No | Yes | Same |
| 17 | scoutsuite | Yes | mcp-server-scoutsuite | **Yes** (scoutsuite-mcp) | No | Yes | Verify scoutsuite-mcp has streamable-http + test |
| 18 | shuffledns | Yes | mcp-server-shuffledns | No | No | Yes | Same |
| 19 | smuggler | Yes | mcp-server-smuggler | **Yes** (smuggler-mcp) | No | Yes | Verify smuggler-mcp has streamable-http + test |
| 20 | sqlmap | Yes | mcp-server-sqlmap | No | No | Yes | Same |
| 21 | sslscan | Yes | mcp-server-sslscan | **Yes** (sslscan-mcp) | No | Yes | Verify sslscan-mcp has streamable-http + test |
| 22 | waybackurls | Yes | mcp-server-waybackurls | No | No | Yes | Same |
| 23 | wpscan | No | — | **Yes** (wpscan-mcp) | No | — | Verify wpscan-mcp has streamable-http + test |

---

## 4. Column Definitions

- **Cyproxio tool:** Directory name in `cyproxio/mcp-for-security-main` (e.g. `alterx-mcp` → alterx).
- **In Acuvity registry?:** Whether `acuvity/mcp-servers-registry-main` has an `mcp-server-*` entry whose `card.json` links to `cyproxio/mcp-for-security` (or `mcp-for-security`).
- **Acuvity image name:** Registry folder / image name (e.g. `acuvity/mcp-server-alterx`).
- **Already Hackerdogs-built?:** We have a `*-mcp` directory at repo root with our own Dockerfile + FastMCP (e.g. `commix-mcp`, `scoutsuite-mcp`).
- **HTTP streamable (Cyproxio source):** Cyproxio code uses only `StdioServerTransport`; no streamable-http in source.
- **HTTP streamable (Acuvity image):** Acuvity runs the same stdio app behind Minibridge, which exposes HTTP/SSE on port 8000 at `/sse` (documented in their README).
- **Action to fix:** What to do so every server meets Hackerdogs §2 (stdio + streamable-http, test.sh, etc.).

---

## 5. Recommended Fix Order

1. **Hackerdogs-built (5):** commix-mcp, scoutsuite-mcp, sslscan-mcp, smuggler-mcp, wpscan-mcp  
   - Confirm each has `MCP_TRANSPORT` / `MCP_PORT` and streamable-http.  
   - Ensure `test.sh` meets full compliance (install, stdio load/call, HTTP load/call).

2. **Acuvity-only (no Hackerdogs build yet):** alterx, amass, arjun, assetfinder, crtsh, ffuf, httpx, katana, masscan, mobsf, nmap, nuclei, oshp (http-headers-security), shuffledns, sqlmap, sslscan (if we use Acuvity image), waybackurls  
   - Either: use Acuvity image and document HTTP/SSE at port 8000 (`/sse`) and align README/mcpServer.json with our port table;  
   - Or: add a Hackerdogs FastMCP wrapper (Python) that shells out to the same CLI tools and supports streamable-http per §2.

3. **Cyproxio-only (not in Acuvity):** cero, gowitness, commix, wpscan  
   - commix and wpscan: we already have Hackerdogs builds; verify and fix as in (1).  
   - cero, gowitness: build from cyproxio source (or add to Acuvity later); ensure stdio + streamable-http (e.g. FastMCP bridge or Node server with streamable-http).

---

## 6. Notes

- **Ports:** Acuvity uses 8000 per server (or configurable in values). We reserve 8000–8010; so when documenting Acuvity-based servers, use distinct ports or note “Acuvity default 8000” and avoid conflict with our reserved range.
- **Phase 2 first 5:** We already added config-only entries for acuvity-mcp-server-alterx-mcp, amass, arjun, assetfinder, atlas-docs (atlas-docs is not Cyproxio). The table above focuses on the **Cyproxio** intersection only.

---

## 7. Minibridge code review (local copy)

**Location:** `tools-to-migrate-to-mcp/acuvity/minibridge-main` (Acuvity’s [minibridge](https://github.com/acuvity/minibridge) repo, copied for reference.)

**What Minibridge is:** A **Go** binary that acts as a frontend–backend bridge. The **frontend** listens on HTTP and exposes MCP over HTTP; the **backend** runs the real MCP server (e.g. Cyproxio Node) via **stdio** only. So the underlying MCP server never speaks HTTP — Minibridge does.

**Architecture (from code):**

- **AIO mode** (`minibridge aio -- <command> [args]`): Single process. Frontend listens on `--listen` (e.g. `:8000`); backend is a subprocess started with the given command (e.g. `node /app/build/index.js alterx`). Communication: frontend ↔ backend over an in-process carrier (e.g. memconn); backend talks **stdio** to the child.
- **Frontend HTTP** (`pkgs/frontend/http.go`): Serves three configurable endpoints (defaults in `pkgs/frontend/options.go`):
  - **`/mcp`** — MCP streamable (proto 2025-03-26): POST with JSON body, `Mcp-Session-Id` header, session-based; responses streamed as `text/event-stream`.
  - **`/sse`** — Event stream (proto 2024-11-05): GET with `Accept: text/event-stream`; long-lived SSE connection.
  - **`/message`** — Message endpoint (proto 2024-11-05).
- **Backend client** (`pkgs/backend/client/stdio.go`): Spawns the MCP server as a subprocess (`exec.CommandContext`), connects to its stdin/stdout. So Cyproxio’s Node server only sees stdio; Minibridge translates between HTTP and stdio.
- **Acuvity container** (from registry `mcp-server-alterx`): `entrypoint.sh` sets `MINIBRIDGE_LISTEN=":8000"` and runs `minibridge aio -- node /app/build/index.js alterx`. The image contains both the Minibridge binary and the Cyproxio Node build; no HTTP in the Node code.

**Why Hackerdogs avoids Minibridge:** We want one stack (FastMCP in Python) with native stdio + streamable-http, no extra Go bridge or Acuvity image. Our servers use `MCP_TRANSPORT` / `MCP_PORT` and FastMCP’s built-in streamable-http; no Minibridge process. The audit table’s “HTTP streamable (Acuvity image)” means “Minibridge exposes /sse and /mcp on 8000”; our “HTTP streamable” is FastMCP’s own transport.
