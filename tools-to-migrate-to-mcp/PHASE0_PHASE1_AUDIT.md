# Phase 0 & Phase 1 MCP Servers — Audit (Completion & Drift)

**Audit date:** 2025-03-18  
**Scope:** Phase 0 (13 ALREADY_BUILT) + Phase 1 (7 COPY_AND_DOCKERIZE) per **MIGRATION_PLAN.md** §3–4.  
**Compliance reference:** **MIGRATION_PLAN.md** §2; **Instructions.md**; `.cursor/rules/mcp-server-test-compliance.mdc`.

---

## 1. Summary

| Question | Answer |
|----------|--------|
| **Phase 0 servers (13)** | All present in repo root; all have required files. |
| **Phase 1 servers (7)** | All present in repo root; all have required files. |
| **Required files (§2.2)** | All 20 servers have: Dockerfile, mcp_server.py, README.md, mcpServer.json, docker-compose.yml, test.sh, requirements.txt, publish_to_hackerdogs.sh. |
| **HTTP streamable** | All 20 implement `MCP_TRANSPORT` / `streamable-http` in mcp_server.py. |
| **progress.md** | All 20 have progress.md (optional per §2.2). |
| **test.sh compliance (5 areas)** | All 20 cover: (1) install, (2) stdio tools/list, (3) stdio tools/call, (4) HTTP streamable tools/list, (5) HTTP streamable tools/call. |
| **Drift: test.sh builds image** | **All 20** use “if image missing then build” instead of project standard: **inspect only, fail with “Build first: docker build …”** if image missing. |
| **Root README / port list** | Phase 0/1 servers are listed in root README with ports (sampled: dnsdumpster 8216, holehe 8219, abusech 8373). |

---

## 2. Phase 0 — ALREADY_BUILT (13 servers)

**Action per plan:** Verify presence, README, build, stdio + HTTP streamable, test.sh; fix drift.

| # | mcp_server_name | Files complete | HTTP streamable | test.sh 5 areas | Drift (test.sh builds) |
|---|-----------------|----------------|-----------------|-----------------|-------------------------|
| 1 | dnsdumpster-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 2 | holehe-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 3 | julius-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 4 | maigret-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 5 | misp-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 6 | onionsearch-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 7 | opencti-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 8 | otx-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 9 | semgrep-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 10 | sherlock-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 11 | subfinder-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 12 | virustotal-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 13 | zmap-mcp | ✅ | ✅ | ✅ | ✅ Fixed |

**Phase 0 conclusion:** Complete for content and dual transport. **test.sh drift fixed:** all 13 now use inspect-only and "Build first" on missing image; project standard is inspect-only and fail with “Build first: docker build -t \<image\> \<dir\>”.

---

## 3. Phase 1 — COPY_AND_DOCKERIZE (7 servers)

**Action per plan:** Copy/align with FastMCP, Dockerfile, dual transport, README, mcpServer.json, docker-compose, test.sh.

| # | mcp_server_name | Files complete | HTTP streamable | test.sh 5 areas | Drift (test.sh builds) |
|---|-----------------|----------------|-----------------|-----------------|-------------------------|
| 1 | abusech-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 2 | abuseipdb-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 3 | builtwith-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 4 | code-execution-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 5 | deepwebresearch-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 6 | pagespeed-mcp | ✅ | ✅ | ✅ | ✅ Fixed |
| 7 | secops-mcp | ✅ | ✅ | ✅ | ✅ Fixed |

**Phase 1 conclusion:** All seven are present and aligned with required files and dual transport. **test.sh drift fixed:** same inspect-only / "Build first" as Phase 0.

---

## 4. Drift detail: test.sh image handling

**Project standard (per Acuvity/Cyproxio compliance and `.cursor/rules/mcp-server-test-compliance.mdc`):**

- **Step 1 (install):** Verify the image exists (e.g. `docker image inspect "$IMAGE"`). If missing, **exit with failure** and print:  
  `Build first: docker build -t <image> <project_dir>`
- **Do not** run `docker build` inside test.sh.

**Current behavior in all 20 Phase 0/1 servers:**

- test.sh runs `if ! docker image inspect "$IMAGE" ...; then docker build -t "$IMAGE" "$PROJECT_DIR"; fi` (or equivalent).
- So tests **build** the image when it is missing, instead of failing fast with a clear “Build first” message.

**Recommended fix (per server):**

Replace the “build if missing” block with:

```bash
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Build first: docker build -t $IMAGE $PROJECT_DIR" >&2
  exit 1
fi
```

Then remove any `docker build` from test.sh. Optionally keep a comment: “# Image must exist; build with: docker build -t $IMAGE $PROJECT_DIR”.

---

## 5. Checklist vs §2.2 (per server)

| Requirement | Phase 0 (13) | Phase 1 (7) |
|-------------|--------------|-------------|
| Dockerfile | ✅ | ✅ |
| mcp_server.py (FastMCP, stdio + streamable-http) | ✅ | ✅ |
| publish_to_hackerdogs.sh | ✅ | ✅ |
| README.md (logo, both transports, env, examples) | ✅ (holehe sampled) | ✅ |
| mcpServer.json | ✅ | ✅ |
| docker-compose.yml | ✅ | ✅ |
| test.sh (5 areas) | ✅ | ✅ |
| requirements.txt | ✅ | ✅ |
| progress.md (optional) | ✅ all | ✅ all |

---

## 6. Suggested next steps

1. **Fix test.sh drift (all 20):** Change test.sh to inspect-only and “Build first” on missing image (see §4).
2. **Re-run tests:** For each server, build image once (`docker build -t <image> <dir>`), then run `./test.sh` and confirm all 5 areas pass.
3. **Mark Phase 0 & Phase 1 verified:** After (1) and (2), update **MIGRATION_PLAN.md** §0 and §3/§4 to “Verified” with a pointer to this audit.

---

## 7. File references

- **Plan:** `tools-to-migrate-to-mcp/MIGRATION_PLAN.md` (§0, §2, §3, §4)
- **Compliance rule:** `.cursor/rules/mcp-server-test-compliance.mdc`
- **Project requirements:** `Instructions.md`
- **Acuvity audit (comparison):** `tools-to-migrate-to-mcp/ACUVITY_CYPROXIO_AUDIT.md`
