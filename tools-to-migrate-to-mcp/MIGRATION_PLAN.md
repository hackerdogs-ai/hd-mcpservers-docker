# MCP Servers Migration Plan (Detailed)

This plan is based on **migration_audit.csv** and **g-tools-audit.csv**. It lists every server by name and defines how to migrate them into **hd-mcpservers-docker** (FastMCP + Docker, stdio + HTTP streamable).

---

## 0. Current state (updated)

| Milestone | Status | Notes |
|-----------|--------|--------|
| **Acuvity/Cyproxio 23** | **Done** | All 23 migrated to root `*-mcp/` (e.g. alterx-mcp, amass-mcp, …). FastMCP, stdio + streamable-http. Image built and `test.sh` passed for all. See **ACUVITY_CYPROXIO_AUDIT.md** §2.1. |
| **Phase 0 (13 ALREADY_BUILT)** | **Verified** | All 13 present; files complete; stdio + HTTP streamable; test.sh has 5 areas; test.sh inspect-only, "Build first" if image missing. See **PHASE0_PHASE1_AUDIT.md**. |
| **Phase 1 (7 COPY_AND_DOCKERIZE)** | **Verified** | All 7 present; files complete; stdio + HTTP streamable; test.sh has 5 areas; test.sh drift fixed. See **PHASE0_PHASE1_AUDIT.md**. |
| **Phase 2 (80 COPY_DOCKER_CONFIG)** | Partial | 23 Acuvity/Cyproxio servers done (root names: alterx-mcp … wpscan-mcp). ~57 remaining from export CSV. |
| **Phase 3 (112 BUILD_NEW)** | Pending | New FastMCP servers from LangChain/CSV. |
| **Phase 4 (75 REFACTOR_TO_DOCKER)** | Pending | npx/uvx → Docker. |
| **Phase 5 (10 REMOTE_ONLY)** | Pending | Document only. |

**Acuvity 23 root folders (done):** alterx-mcp, amass-mcp, arjun-mcp, assetfinder-mcp, cero-mcp, commix-mcp, crtsh-mcp, ffuf-mcp, gowitness-mcp, http-headers-security-mcp, httpx-mcp, katana-mcp, masscan-mcp, mobsf-mcp, nmap-mcp, nuclei-mcp, scoutsuite-mcp, shuffledns-mcp, smuggler-mcp, sqlmap-mcp, sslscan-mcp, waybackurls-mcp, wpscan-mcp.

---

## 1. Audit Summary

| Action | Count | Description |
|--------|-------|-------------|
| **ALREADY_BUILT** | 13 | Already in repo; verify only. |
| **BUILD_NEW** | 112 | New Docker/FastMCP server from LangChain source or export CSV. |
| **COPY_AND_DOCKERIZE** | 7 | Existing MCP code — copy into repo and add Docker/FastMCP. |
| **COPY_DOCKER_CONFIG** | 80 | Docker config in export CSV — copy/verify into repo. |
| **REFACTOR_TO_DOCKER** | 75 | Currently npx/uvx — refactor to Docker (optionally FastMCP). |
| **REMOTE_ONLY** | 10 | Remote streamable-http only; no local build. |

**Target format for all local servers:** `docker_fastmcp` (FastMCP in Docker, stdio **and** HTTP-streamable — both required).

**Which 13 are ALREADY_BUILT?** dnsdumpster-mcp, holehe-mcp, julius-mcp, maigret-mcp, misp-mcp, onionsearch-mcp, opencti-mcp, otx-mcp, semgrep-mcp, sherlock-mcp, subfinder-mcp, virustotal-mcp, zmap-mcp (see Phase 0 table below for tool names and source notes).

---

## 2. Project requirements: compliance, code quality, documentation, HTTP-streamable

**Every MCP server migrated into this project must meet the same compliance, code quality, documentation, and capability standards.** No server is considered complete until it satisfies the requirements below. This applies to Phase 0 (verification), Phase 1, 2, 3, and 4 migrations.

### 2.1 Mandatory: HTTP-streamable endpoint

- **Every MCP server must support the HTTP-streamable transport** in addition to stdio.
- The server must respect `MCP_TRANSPORT` (e.g. `stdio` or `streamable-http`) and, when `streamable-http`, listen on `MCP_PORT` (configurable, with a default that does not conflict with other tools in the repo).
- Reserved ports (do not use): 80, 8000–8010, 8501–8510, 9000–9010, and other well-known ports of popular apps. Assign a unique port per server and maintain the tool/port list in the root **README.md**.
- **Verification:** `test.sh` must include at least one test that runs the server with `MCP_TRANSPORT=streamable-http`, hits the HTTP endpoint (e.g. init or tools/list), and asserts a successful response.

Reference: project **Instructions.md** and existing servers (e.g. **holehe-mcp**): `mcp_server.py` uses `mcp.run(transport="streamable-http", host="0.0.0.0", port=MCP_PORT)` when `MCP_TRANSPORT != "stdio"`.

### 2.2 Compliance and capability checklist (per server)

Each server directory `[tool-name]-mcp/` must contain:

| Requirement | Description |
|-------------|-------------|
| **Dockerfile** | Multi-stage where appropriate; non-root user; `MCP_TRANSPORT` default `stdio`; tool and FastMCP runtime installed. |
| **mcp_server.py** | FastMCP wrapper over the tool; descriptive tool name(s) and parameters; **support both stdio and streamable-http** via `MCP_TRANSPORT` / `MCP_PORT`; robust error handling and timeouts; logging to stderr. |
| **publish_to_hackerdogs.sh** | Build and publish script; supports `--build`, `--publish`, `--help`; multi-arch (e.g. linux/amd64, linux/arm64) where applicable. |
| **README.md** | Hackerdogs logo (https://hackerdogs.ai/images/logo.png); description of the tool and MCP wrapper; build, deployment, and usage steps; **Docker Run (stdio)** and **Docker Run (HTTP streamable mode)** examples; MCP client configuration (stdio and HTTP); env vars (e.g. `MCP_TRANSPORT`, `MCP_PORT`, any API keys); tools reference and example prompts. |
| **mcpServer.json** | Config for Claude/Cursor; includes `MCP_TRANSPORT` (and `MCP_PORT` if needed) in env; docker command/args pattern. |
| **docker-compose.yml** | Service definition; port mapping for HTTP streamable; env `MCP_TRANSPORT=streamable-http` (or document override). |
| **test.sh** | **Compliance:** Must include all five areas per `.cursor/rules/mcp-server-test-compliance.mdc`: (1) install, (2) stdio tools/list, (3) stdio tools/call (simple tool), (4) HTTP streamable tools/list, (5) HTTP streamable tools/call (simple tool). Use `Accept: application/json, text/event-stream` on HTTP; capture session id for HTTP; proper cleanup; pass/fail summary. |
| **requirements.txt** | Python deps (e.g. `fastmcp`); pinned versions where appropriate. |
| **progress.md** | Optional but recommended: checklist of setup steps and port assignment for tracking. |

### 2.3 Code quality

- Use **FastMCP** only; no ad-hoc MCP implementations.
- Async tool handlers where I/O or subprocess is used; timeouts on all long-running operations.
- Structured logging (e.g. `logging.basicConfig` to stderr, `logger.info`/`warning`/`error`); no secrets in logs.
- Subprocess output captured and returned in a structured way (e.g. JSON or consistent text); parse and validate where applicable.

### 2.4 Migration acceptance criteria

Before marking any migrated server as **done**:

1. **HTTP-streamable:** Server runs with `MCP_TRANSPORT=streamable-http` and responds to MCP HTTP requests on the assigned port.
2. **Compliance:** All files from §2.2 are present and conform to the project pattern.
3. **Code quality:** Meets §2.3; no known security or stability issues.
4. **Documentation:** README covers tool description, both transports, env vars, and example prompts; server is listed in the root README with its port.
5. **Tests:** `test.sh` passes for both stdio and HTTP streamable modes.

---

## 3. Phase 0 — ALREADY_BUILT (Verify Only)

**The 13 servers below are already in the repo.** Audit completed: see **PHASE0_PHASE1_AUDIT.md**. All 13 have required files, dual transport, test.sh with 5 areas; test.sh now inspect-only, "Build first" if image missing.

| # | Tool name (audit) | mcp_server_name | Source / notes |
|---|-------------------|-----------------|----------------|
| 1 | dnsdumpster | **dnsdumpster-mcp** | LangChain → migrated |
| 2 | holehe | **holehe-mcp** | LangChain → migrated |
| 3 | Julius MCP Server | **julius-mcp** | Already in repo |
| 4 | maigret | **maigret-mcp** | LangChain → migrated |
| 5 | misp | **misp-mcp** | LangChain → migrated |
| 6 | onionsearch | **onionsearch-mcp** | LangChain → migrated |
| 7 | opencti | **opencti-mcp** | LangChain → migrated |
| 8 | otx | **otx-mcp** | LangChain → migrated |
| 9 | Semgrep MCP SERVER | **semgrep-mcp** | Already in repo |
| 10 | sherlock | **sherlock-mcp** | LangChain → migrated |
| 11 | subfinder | **subfinder-mcp** | LangChain → migrated |
| 12 | virustotal | **virustotal-mcp** | LangChain → migrated |
| 13 | zmap | **zmap-mcp** | LangChain → migrated |

**Action:** Audit done; test.sh drift fixed. Re-run test.sh after building image to confirm all 5 areas pass.

---

## 4. Phase 1 — COPY_AND_DOCKERIZE (7 servers)

**Audit completed:** see **PHASE0_PHASE1_AUDIT.md**. All 7 present with required files and dual transport; test.sh drift fixed.

Source code exists in repo; add Dockerfile and align with FastMCP pattern.

| # | Tool name | mcp_server_name | Source path | Format | Env / notes |
|---|-----------|-----------------|-------------|--------|-------------|
| 1 | abusech | **abusech-mcp** | `tools-to-migrate-to-mcp/osint/abusech-mcp-main/` | Python | ABUSECH_API_KEY |
| 2 | abuseipdb | **abuseipdb-mcp** | `tools-to-migrate-to-mcp/osint/mcp-abuseipdb-main/` | Python | ABUSEIPDB_API_KEY |
| 3 | builtwith | **builtwith-mcp** | `tools-to-migrate-to-mcp/osint/builtwith/` | Node | BUILTWITH_API_KEY; consider Python rewrite |
| 4 | code-execution | **code-execution-mcp** | `tools-to-migrate-to-mcp/mcp-server-code-execution-mode-main/` | uvx | Docker + FastMCP refactor |
| 5 | deepwebresearch | **deepwebresearch-mcp** | `tools-to-migrate-to-mcp/mcp-DEEPwebresearch-main/` | npx/TS | Docker rewrite to Python/FastMCP |
| 6 | pagespeed | **pagespeed-mcp** | `tools-to-migrate-to-mcp/osint/pagespeed-mcp/` | TS | PAGESPEED_API_KEY; Docker rewrite |
| 7 | secops | **secops-mcp** | `tools-to-migrate-to-mcp/secops-mcp-main/` | Python | Has Dockerfile; refactor to repo standard |

**Steps per server:** Copy source to `/<mcp_server_name>/`, add/align Dockerfile (Python 3.11+ slim, non-root), ensure FastMCP entrypoint, add README, mcpServer.json, docker-compose if missing; build and add to main README.

---

## 5. Phase 2 — COPY_DOCKER_CONFIG (80 servers)

Docker config is in export CSV. Obtain image/env/command and add `/<mcp_server_name>/` with README, mcpServer.json, and optional Dockerfile or upstream image reference.

**Done (23):** Acuvity/Cyproxio intersection — migrated as root folders **alterx-mcp**, **amass-mcp**, **arjun-mcp**, **assetfinder-mcp**, **cero-mcp**, **commix-mcp**, **crtsh-mcp**, **ffuf-mcp**, **gowitness-mcp**, **http-headers-security-mcp**, **httpx-mcp**, **katana-mcp**, **masscan-mcp**, **mobsf-mcp**, **nmap-mcp**, **nuclei-mcp**, **scoutsuite-mcp**, **shuffledns-mcp**, **smuggler-mcp**, **sqlmap-mcp**, **sslscan-mcp**, **waybackurls-mcp**, **wpscan-mcp**. See **ACUVITY_CYPROXIO_AUDIT.md**.

### Full list (80)

| # | Tool name (audit) | mcp_server_name | Status |
|---|-------------------|-----------------|--------|
| 1 | AACT Clinical Trials MCP Server | ctgov-mcp-docker-mcp | Pending |
| 2 | Alpha Vantage MCP | alphavantage-mcp | Pending |
| 3 | Alterx MCP | alterx-mcp (root) | Done |
| 4 | Amass MCP Server | amass-mcp (root) | Done |
| 5 | Arjun MCP Server | arjun-mcp (root) | Done |
| 6 | Assetfinder MCP Server | assetfinder-mcp (root) | Done |
| 7 | Atlas Docs MCP Server | acuvity-mcp-server-atlas-docs-mcp | Pending |
| 8 | Atlassian MCP Server | acuvity-mcp-server-atlassian-mcp | Pending |
| 9 | Bing Search MCP server | acuvity-mcp-server-bing-search-mcp | Pending |
| 10 | Brave Search MCP Server | acuvity-mcp-server-brave-search-mcp | Pending |
| 11 | Calculator MCP Server | acuvity-mcp-server-calculator-mcp | Pending |
| 12 | Chroma MCP Server | acuvity-mcp-server-chroma-mcp | Pending |
| 13 | Code Runner MCP Server | mcp-server-code-runner-mcp | Pending |
| 14 | Cortex MCP server | cortex-mcp | Pending |
| 15 | Crtsh MCP Server | crtsh-mcp (root) | Done |
| 16 | Crunchbase MCP Server | crunchbase-mcp | Pending |
| 17 | Docker MCP server | acuvity-mcp-server-docker-mcp | Pending |
| 18 | DuckDuckGo MCP server | duckduckgo-mcp | Pending |
| 19 | DuckDuckGo Search MCP Server (Acuvity) | acuvity-mcp-server-duckduckgo-mcp | Pending |
| 20 | Edgar Tools MCP Server | edgartools-mcp-server-mcp | Pending |
| 21 | EduData Mcp Server | edu-data-mcp | Pending |
| 22 | Eleven Labs MCP Server | acuvity-mcp-server-elevenlabs-mcp | Pending |
| 23 | Everything Wrong MCP Server | acuvity-mcp-server-everything-wrong-mcp | Pending |
| 24 | Fetch Mcp Server | acuvity-mcp-server-fetch-mcp | Pending |
| 25 | FFUF MCP Server | ffuf-mcp (root) | Done |
| 26 | Financial Datasets MCP | financial-datasets-mcp | Pending |
| 27 | Firecrawl MCP Server | acuvity-mcp-server-firecrawl-mcp | Pending |
| 28 | Flights MCP | flights-mcp | Pending |
| 29 | FRED MCP SERVER | fred-mcp | Pending |
| 30 | Google Maps MCP Server | acuvity-mcp-server-google-maps-mcp | Pending |
| 31 | Grafana MCP Server | acuvity-mcp-server-grafana-mcp | Pending |
| 32 | Harness MCP Server | acuvity-mcp-server-harness-mcp | Pending |
| 33 | httpx MCP | httpx-mcp (root) | Done |
| 34 | Hyperbrowser MCP Server | acuvity-mcp-server-hyperbrowser-mcp | Pending |
| 35 | Kagi Search MCP Server | acuvity-mcp-server-kagisearch-mcp | Pending |
| 36 | Katana MCP Server | katana-mcp (root) | Done |
| 37 | Mapbox MCP Server | mapboxserver-mcp | Pending |
| 38 | Marine Traffic MCP | marinetraffic-mcp | Pending |
| 39 | Masscan MCP | masscan-mcp (root) | Done |
| 40 | MCP Server Everything | acuvity-mcp-server-everything-mcp | Pending |
| 41 | Microsoft Azure MCP Server | acuvity-mcp-server-azure-mcp | Pending |
| 42 | Microsoft Graph MCP Server | acuvity-mcp-server-microsoft-graph-mcp | Pending |
| 43 | Minio AIStor MCP Server (Official) | aistor-mcp | Pending |
| 44 | N2YO MCP | n2yo-mcp | Pending |
| 45 | NetUtils | netutils-mcp | Pending |
| 46 | Nmap MCP Server | nmap-mcp (root) | Done |
| 47 | Notion MCP Server | acuvity-mcp-server-notion-mcp | Pending |
| 48 | Nuclei MCP Server | nuclei-mcp (root) | Done |
| 49 | OCR MCP Server | ocr-mcp | Pending |
| 50 | Open Legal Compliance MCP | open-legal-mcp | Pending |
| 51 | OpenCV MCP Server | opencv-mcp-server-mcp | Pending |
| 52 | OSHP MCP Server | acuvity-mcp-server-oshp-mcp | Pending |
| 53 | PDF Reader MCP Server (Sylphx) | pdf-reader-mcp | Pending |
| 54 | PentestAgent MCP | pentest-agent-mcp | Pending |
| 55 | Playwright MCP Server | acuvity-mcp-server-playwright-mcp | Pending |
| 56 | Polygon MCP server | polygon-mcp | Pending |
| 57 | PubMed MCP | pubmed-mcp | Pending |
| 58 | Reddit MCP Server | reddit-mcp-server-mcp | Pending |
| 59 | RSS MCP Server | rss-mcp | Pending |
| 60 | Scan URL MCP server | scan-url-mcp | Pending |
| 61 | Scout Suite MCP | scoutsuite-mcp (root) | Done |
| 62 | Scrapezy MCP Server | acuvity-mcp-server-scrapezy-mcp | Pending |
| 63 | SEC Edgar MCP Server | sec-edgar-mcp | Pending |
| 64 | Sentry MCP Server | acuvity-mcp-server-sentry-mcp | Pending |
| 65 | Shodan MCP | shodan-mcp | Pending |
| 66 | shuffledns MCP Server | shuffledns-mcp (root) | Done |
| 67 | Slack MCP Server | slack-mcp | Pending |
| 68 | Slack MCP Server (Acuvity) | acuvity-mcp-server-slack-mcp | Pending |
| 69 | Smuggler MCP Server | smuggler-mcp (root) | Done |
| 70 | SQLMAP MCP Server | sqlmap-mcp (root) | Done |
| 71 | SSLScan MCP | sslscan-mcp (root) | Done |
| 72 | Trivy Security MCP server | trivy-security-mcp | Pending |
| 73 | USGS MCP | earthquake-mcp | Pending |
| 74 | Waybackurls MCP | waybackurls-mcp (root) | Done |
| 75 | Wiremcp | wiremcp-mcp | Pending |
| 76 | World Bank MCP | world-bank-mcp | Pending |
| 77 | Yahoo Finance MCP SERVER | yfmcp-mcp | Pending |
| 78 | YaraFlux MCP server | yaraflux-mcp-server-mcp | Pending |
| 79 | YouTube MCP Server | youtube-mcp | Pending |
| 80 | Zscaler MCP Server | zscaler-mcp-server-mcp | Pending |

**Priority for Phase 2:** Start with OSS/high-demand: duckduckgo-mcp, shodan-mcp, acuvity-mcp-server-nuclei-mcp, acuvity-mcp-server-nmap-mcp, acuvity-mcp-server-ffuf-mcp, acuvity-mcp-server-sqlmap-mcp, ocr-mcp, pdf-reader-mcp, cortex-mcp, netutils-mcp; then the rest.

---

### Phase 3 — BUILD_NEW (112 tools → group into fewer servers)

**Effort: High.** New FastMCP servers from LangChain source or export CSV. **Strategy:** Group into single servers where possible.

**Group into single servers:** abstract-mcp (10 AbstractAPI tools), abusech-mcp (Phase 1 + 4 report tools), browserless-mcp (7 tools), victorialogs-mcp (12 tools), extend virustotal-mcp (6 report tools), webc-mcp (30 WebC tools).

**BUILD_NEW from LangChain (high priority):** abstract-mcp, abusech-mcp, adblock-mcp, adguard-dns-mcp, ahmia-mcp, amass-mcp, apple-itunes-mcp, archiveorg-mcp, arin-mcp, baidusearch-mcp, bevigil-mcp, bitbucket-mcp, bravesearch-mcp, browserless-mcp, certgraph-mcp, cloud-datacenter-mcp, crawl4ai-mcp, exiftool-mcp, masscan-mcp, name-server-mcp, nuclei-mcp, owasp-zap-mcp, phoneinfoga-mcp, scrapy-mcp, waybackurls-mcp, webc-mcp, whatsmyname-mcp. **Plus:** AbstractAPI (9), AbuseCH reports (4), Alien Vault (4), Browserless (6), certgraph/Mermaid/Graphviz/VictoriaLogs/VirusTotal/WebC from export CSV; excel-tools, file-operations, graphviz-dot, mermaid, ocr-tools, powerpoint-tools, visualization-tools from prodx/osint. See **migration_audit.csv** rows with action BUILD_NEW for the full 112.

---

### Phase 4 — REFACTOR_TO_DOCKER (75 servers, full list)

**Effort: Medium–High.** Currently npx or uvx; target Docker (optionally FastMCP). Prefer **wrap in Docker** (Dockerfile runs npx/uvx).

**All 75 mcp_server_name values:** search1api-mcp, ai-humanizer-mcp, aws-api-mcp, aws-postgres-mcp, aws-bedrock-agentcore-mcp, aws-bedrock-custom-model-mcp, aws-cloudtrail-mcp, aws-cloudwatch-appsignals-mcp, aws-cloudwatch-mcp, aws-core-mcp, aws-documentation-mcp, aws-documentdb-mcp, aws-aurora-dsql-mcp, aws-dynamodb-mcp, aws-ecs-mcp, aws-eks-mcp, aws-iam-mcp, aws-mq-mcp, aws-neptune-mcp, aws-network-mcp, aws-prometheus-mcp, aws-redshift-mcp, aws-s3-tables-mcp, aws-serverless-mcp, aws-sns-sqs-mcp, aws-stepfunctions-mcp, aws-well-architected-security-mcp, azure-mcp, baidu-search-mcp-server-mcp, brave-search-mcp, brightdata-mcp-server-mcp, chrome-devtools-mcp, clinicaltrialsgov-mcp-server-mcp, cloudflare-mcp, context7-mcp, rapidapi-hub-reverse-image-search-by-copyseeker-mcp, dns-mcp-server-mcp, dnstwist-mcp, exa-mcp, exiftool-agent-mcp, fetch-mcp, firecrawl-mcp, geocoding-mcp, gitlab-mcp, globalping-mcp, scc-mcp, google-threat-intelligence-mcp, greynoise-mcp, hibp-mcp, imf-data-mcp, iplocate-mcp, jira-mcp, ms-fabric-rti-mcp, nasa-mcp, notion-mcp, octagon-mcp-server-mcp, octocode-mcp, osm-mcp-server-mcp, openfda-mcp, pinecone-mcp, postman-mcp, puppeteer-mcp, reddit-mcp, s3-mcp-server-mcp, sentry-mcp, serper-search-mcp, splunk-mcp, steampipe-mcp, stripe-mcp, terraform-mcp, tomtom-mcp, variflight-mcp, whois-mcp, winston-ai-mcp, youtube-transcript-mcp.

**Options per server:**
- **A. Wrap in Docker:** Keep existing Node/Python server; Dockerfile runs `npx`/`uvx` inside container. Fastest path; same behavior.
- **B. Rewrite to FastMCP:** New Python FastMCP server that replicates the tool behavior (API clients, CLI wrappers). Best long-term; more work.

**Recommendation:** Prefer A for speed and consistency; move to B when we need to align with repo patterns (single runtime, fewer moving parts). Document which are “wrapped” vs “native FastMCP.”

**Steps:**
1. Create `/<mcp_server_name>/` with Dockerfile that runs the existing server (npx/uvx) and exposes stdio or HTTP.
2. Add `README.md` (env vars, API keys), `mcpServer.json`.
3. If the server does not speak MCP over stdio/HTTP, add a small adapter or choose B.

---

### Phase 5 — REMOTE_ONLY (10 servers, full list)
**Effort: None.** No local build; document in main README as remote streamable-http.

| # | Tool name (audit) | mcp_server_name |
|---|-------------------|-----------------|
| 1 | Censys MCP Server | censys-platform-mcp |
| 2 | Docker MCP Toolkit Gateway | mcp-docker-mcp |
| 3 | GitHub MCP Server | github-mcp |
| 4 | Hackerdogs MCP Server | hackerdogs-mcp-server-mcp |
| 5 | MITRE ATT&CK MCP Server | mitre-attack-remote-mcp |
| 6 | Prowler MCP Server | prowler-mcp |
| 7 | SerpApi MCP Server | serpapi-mcp |
| 8 | Tavily MCP Server | tavily-remote-mcp |
| 9 | WhoisXML MCP Server | whoisxmlapi-mcp |
| 10 | XPoz MCP Server | xpoz-mcp-server-mcp |

**Action:** List these in the repo’s “Remote / streamable-http only” section with endpoint/docs links so users know they are available but not built in this repo.

---

## 8. Priority Order Within Phases

- **High (audit priority):** abstract, abusech, adblock, adguard-dns, ahmia, amass, abuseipdb, builtwith, code-execution, deepwebresearch, masscan, nuclei, owasp-zap, phoneinfoga, scrapy, secops, waybackurls, webc, whatsmyname, etc.
- **Medium:** COPY_DOCKER_CONFIG and REFACTOR entries, plus BUILD_NEW API/OSS tools (AbstractAPI per-tool, Browserless, VictoriaLogs, VirusTotal reports, WebC, etc.).
- **Low:** REMOTE_ONLY (document only), duplicate or low-demand tools.

---

## 9. Repo Conventions to Apply

- **Naming:** One directory per MCP server: `/<mcp_server_name>/` (e.g. `abusech-mcp`, `abstract-mcp`).
- **Docs:** Each server has a `README.md` with at least: what it does, tools list, env vars, Docker run and docker-compose examples, example prompts.
- **Config:** `mcpServer.json` (or equivalent) for Cursor/Hackerdogs with image name, transport, env.
- **Docker:** Dockerfile with non-root user, minimal base (e.g. python:3.11-slim), explicit ports if HTTP (e.g. 8219), and multi-arch where supported.
- **Main README:** Update tool registry tables and port list as servers are added.

---

## 10. Suggested Execution Order

**Gate:** All migrated or verified servers must satisfy **§2 (Project requirements)** — including HTTP-streamable endpoint, compliance checklist, code quality, documentation, and test.sh for both transports — before being marked done.

1. **Phase 0** — Verify 13 ALREADY_BUILT; confirm stdio + HTTP-streamable, docs, and port list; fix any drift.
2. **Phase 1** — Complete 7 COPY_AND_DOCKERIZE; for each, add Dockerfile, dual transport, README, mcpServer.json, docker-compose, test.sh per §2.
3. **Phase 2** — Batch COPY_DOCKER_CONFIG; for each, add or align with §2 (ensure HTTP-streamable and full checklist).
4. **Phase 3** — BUILD_NEW in batches; each new server must implement stdio + streamable-http and meet §2.2–2.4.
5. **Phase 4** — REFACTOR_TO_DOCKER; wrapped or rewritten servers must expose HTTP-streamable and pass §2 acceptance criteria.
6. **Phase 5** — Document REMOTE_ONLY in README (no local build; no §2 gate for those).

---

## 11. Tracking

- **migration_audit.csv** — master list; add a column e.g. `migration_phase` (0–5) and `status` (pending | in_progress | done | skipped) to track progress.
- **g-tools-audit.csv** — use for cross-checking tool names, slugs, and categories when adding READMEs and registry entries.

---

## 12. File References

- **Project requirements:** `Instructions.md` (root) — directory structure, required files, stdio + http-streamable requirement, port rules.
- **Phase 0 & Phase 1 audit:** `tools-to-migrate-to-mcp/PHASE0_PHASE1_AUDIT.md` — completion and drift for the 13 ALREADY_BUILT and 7 COPY_AND_DOCKERIZE servers.
- Audit: `tools-to-migrate-to-mcp/migration_audit.csv`
- Tool/catalog: `tools-to-migrate-to-mcp/g-tools-audit.csv`
- LangChain sources: `tools-to-migrate-to-mcp/osint/*.py`, `tools-to-migrate-to-mcp/ti/*.py`, `tools-to-migrate-to-mcp/prodx/*.py`, `tools-to-migrate-to-mcp/*.py`, `tools-to-migrate-to-mcp/feeds/*.py`
- Existing server example: `holehe-mcp/` (README, Dockerfile, mcp_server.py with dual transport, mcpServer.json, docker-compose, test.sh for stdio + HTTP streamable)

---

## 13. Current state & suggested next steps

**Current state:** See **§0** above. Acuvity/Cyproxio 23 are **done** (image built, test.sh passed, dual transport). Phase 0–5 are otherwise pending.

**Suggested next steps (in order):**

1. **Phase 0** — Verify the 13 ALREADY_BUILT servers (dnsdumpster-mcp, holehe-mcp, julius-mcp, maigret-mcp, misp-mcp, onionsearch-mcp, opencti-mcp, otx-mcp, semgrep-mcp, sherlock-mcp, subfinder-mcp, virustotal-mcp, zmap-mcp): confirm presence, README, image builds, stdio + HTTP streamable, and test.sh (no build inside test; fail with “Build first” if image missing). Fix any drift.
2. **Phase 1** — Complete the 7 COPY_AND_DOCKERIZE servers (abusech-mcp, abuseipdb-mcp, builtwith-mcp, code-execution-mcp, deepwebresearch-mcp, pagespeed-mcp, secops-mcp) per §2: Dockerfile, dual transport, README, mcpServer.json, docker-compose, test.sh.
3. **Phase 2** — Continue COPY_DOCKER_CONFIG for the remaining ~57 (see table in §5; 23 already done). For each, add or align with §2 (HTTP streamable, checklist, test.sh).
4. **Tracking** — Optionally add `migration_phase` and `status` columns to `migration_audit.csv` (§11) and keep in sync with §0 and §5 table.

End of migration plan.
