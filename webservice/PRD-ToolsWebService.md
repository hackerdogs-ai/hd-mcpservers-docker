# PRD: Tools Web Service (FastAPI)

**Document:** PRD-ToolsWebService.md  
**Location:** `webservice/`  
**Status:** Draft  
**Last Updated:** 2026-03-07  

---

## 1. Overview

### 1.1 Purpose

Build a **FastAPI-based web service/API** that:

- Serves a **catalog of MCP (Model Context Protocol) tools** loaded from cloud storage (S3).
- Exposes **list**, **search**, **get_tool_info**, and **run_tool** endpoints.
- **Runs tools directly** (no LLM): the service uses an MCP client to invoke tools (Docker, npx, uvx) with given parameters and returns results in a **standardized OCSF (Open Cybersecurity Schema Framework)** format.
- Runs in **Docker** with **Docker-in-Docker (DinD)** or Docker socket access to run tool containers; supports **npx** and **uvx** tools by installing Node.js and uv in the webservice image.

### 1.2 Principles

- **No LLM usage:** All tool execution is direct (MCP client → tool process).
- **Use existing libraries:** Caching (e.g. `cachetools`), OCSF (e.g. `ocsf-lib` or `py-ocsf-models`), S3 (boto3), MCP client (FastMCP/mcp). Do not reinvent caching or OCSF.
- **Quality & compliance:** Structured exceptions, logging to stdout/stderr, clear error responses.
- **Multi-platform:** Docker image must run on **Mac and Linux**, **ARM64 and AMD64**.

### 1.3 Reference Data

- Current tools catalog: `webservice/2026-03-07T20-14_export.csv` (CSV export from database with Tool Name, Description, Category, Vendor, Configuration (mcpServers JSON), etc.).
- In-repo MCP server configs: e.g. `naabu-mcp/mcpServer.json` (command, args, env pattern).

---

## 2. Data & Storage

### 2.1 Tools Catalog Source

- **Source:** A single JSON file (or manifest) stored in **S3**.
- **URL:** Provided via **environment variable** (e.g. `TOOLS_CATALOG_S3_URI` or `TOOLS_CATALOG_URL`). Support both S3 URIs (`s3://bucket/key`) and optionally HTTPS URLs if the object is public or pre-signed.
- **Loading:** On startup and when cache expires (see §3.1), the service fetches this object, parses it, and populates the in-memory cache.

### 2.2 Tools Catalog JSON Format (Design)

The catalog JSON **passes MCP server configuration through as-is**. No transformation or flattening: the same `mcpServers` structure used in the CSV `Configuration` column and in `mcpServer.json` files is stored and returned unchanged. This keeps a single source of truth, matches what Cursor and other MCP clients consume, and simplifies migration from CSV (parse and store the Configuration JSON directly).

Recommended **JSON schema** for the S3 object:

```json
{
  "version": "1.0",
  "updated_at": "2026-03-07T20:00:00Z",
  "tools": [
    {
      "id": "aact_clinical_trials_mcp_server_1772085716",
      "name": "AACT Clinical Trials MCP Server",
      "description": "A Model Context Protocol (MCP) server implementation that provides access to the AACT database...",
      "category": "OSINT Tool",
      "vendor": "OSS",
      "tool_type": "mcp_server",
      "is_active": true,
      "is_featured": true,
      "search_terms": ["clinicaltrials", "list_tables", "read_query", "describe_table"],
      "configuration": {
        "mcpServers": {
          "CTGOV-MCP-DOCKER": {
            "args": ["run", "--rm", "-i", "--env", "DB_USER=YOUR_USERNAME", "--env", "DB_PASSWORD=YOUR_PASSWORD", "navisbio/mcp-server-aact:latest"],
            "command": "docker"
          }
        }
      },
      "metadata": {
        "source_code_link": "https://github.com/navisbio/aact_mcp",
        "documentation_url": "https://aact.ctti-clinicaltrials.org/",
        "deployment_model": "Cloud",
        "pricing_model": "Enterprise"
      }
    },
    {
      "id": "ai_text_detector_mcp_1769273865",
      "name": "AI Text Detector MCP",
      "description": "A Model Context Protocol (MCP) server designed to refine AI-generated content...",
      "category": "OSINT Tool",
      "vendor": "Text2Go",
      "tool_type": "mcp_server",
      "is_active": true,
      "configuration": {
        "mcpServers": {
          "ai-humanizer": {
            "args": ["-y", "ai-humanizer-mcp-server"],
            "command": "npx"
          }
        }
      },
      "metadata": {}
    },
    {
      "id": "aws_api_mcp_server_1769395576",
      "name": "AWS API mcp server",
      "description": "The AWS API MCP Server enables AI assistants to interact with AWS services...",
      "category": "Cloud Security Posture Management (CSPM)",
      "vendor": "AWS",
      "tool_type": "mcp_server",
      "is_active": true,
      "configuration": {
        "mcpServers": {
          "aws-api": {
            "env": {
              "AWS_REGION": "us-east-1",
              "AWS_ACCESS_KEY_ID": "YOUR_AWS_ACCESS_KEY_ID",
              "AWS_SECRET_ACCESS_KEY": "YOUR_AWS_SECRET_ACCESS_KEY"
            },
            "args": ["awslabs.aws-api-mcp-server@latest"],
            "command": "uvx"
          }
        }
      },
      "metadata": {}
    }
  ]
}
```

**Field notes:**

| Field | Description |
|-------|-------------|
| `id` | Unique tool identifier (maps to CSV `ID`). |
| `name` | Display name. |
| `description` | Full description. |
| `category`, `vendor`, `tool_type` | For filtering and display. |
| `is_active`, `is_featured` | For filtering (only active tools by default). |
| `search_terms` | Array of strings for search indexing. |
| `configuration` | **Required. Passed as-is.** The exact MCP config object: `{ "mcpServers": { "<server_name>": { "command", "args", "env" } } }`. Same shape as CSV `Configuration` and `mcpServer.json`. The API returns this unchanged so clients can use it directly (e.g. Cursor, MCP SDKs). |
| `metadata` | Optional links and extra fields. |

**Migration from CSV:** Map each CSV row into one tool object; set `configuration` to the **parsed JSON from the `Configuration` column** with no transformation. If the column is already valid `{ "mcpServers": { ... } }`, use it as-is. Add or derive only top-level fields (id from `ID`, name from `Tool Name`, etc.).

---

## 3. Caching

### 3.1 Requirement

- Tools catalog is **cached in memory**.
- **TTL (time-to-live)** is **configurable** (e.g. env `TOOLS_CACHE_TTL_SECONDS`, default 300).
- After TTL expires, the next request that needs the catalog **reloads from S3** (or configured URL) and refreshes the cache.
- **Use an existing caching library** (e.g. **cachetools** with `TTLCache`). Do not implement a custom TTL cache.

### 3.2 Implementation Notes

- **cachetools:** `TTLCache(maxsize=..., ttl=seconds)` or `@cachetools.func.ttl_cache(maxsize=..., ttl=...)` for a loader function. Ensure thread-safety (e.g. lock) if the same cache is used from multiple workers.
- Cache key: e.g. `"tools_catalog"` for the full list; optional per-tool cache for `get_tool_info` (separate TTL if desired).
- On load failure (S3/network error): retain previous cached data if available and log error to stderr; optionally return 503 until next successful load.

---

## 4. API Endpoints

Base path: e.g. `/api/v1` (configurable). All responses JSON unless noted.

### 4.1 List All Tools

- **Method/Path:** `GET /api/v1/tools`
- **Query (optional):** `active_only=true` (default), `category`, `vendor`, `limit`, `offset`.
- **Behavior:** Return tools from cached catalog, filtered by query params.
- **Response:** `{ "tools": [ { "id", "name", "description", "category", "vendor", "configuration": { "mcpServers": { ... } } } ], "total": N }`. The `configuration` object is passed through as-is from the catalog.

### 4.2 Search Tools

- **Method/Path:** `GET /api/v1/tools/search` or `GET /api/v1/search?q=...`
- **Query:** `q` (required), optional `category`, `limit`, `offset`.
- **Behavior:** Search over `name`, `description`, `search_terms`, `id`, `server_name`. Use simple in-memory search (e.g. substring/term matching); no external search engine required for MVP.
- **Response:** Same shape as list (array of tool summaries + total).

### 4.3 Get Tool Info

- **Method/Path:** `GET /api/v1/tools/{tool_id}` or `POST /api/v1/tools/info` with body `{ "tool_id": "..." }`.
- **Behavior:**
  1. Resolve `tool_id` from cache (catalog). If not found → 404.
  2. Use **MCP client** (FastMCP Python client or official MCP Python client) to connect to the tool:
     - If **command is `docker`:** Run the container (e.g. `docker run ...` with args from config). Ensure Docker is available (DinD or socket). If image not present, **pull from Docker Hub** (or configured registry) then run.
     - If **command is `npx`:** Run inside the webservice environment where **Node.js/npx is installed** (or in a dedicated sidecar); for Docker-based webservice, **install Node.js in the image** so `npx` can be executed.
     - If **command is `uvx`:** Run inside the webservice environment where **uv/uvx is installed**; **install uv in the Docker image** so `uvx` can be executed.
  3. Once the MCP server is running (stdio transport), call **list tools** (and optionally list resources/prompts) to get full tool schema.
  4. Return **full exposure** of the tool as an MCP server would: **tools** (name, description, input schema for each), **resources** (if any), **prompts** (if any). No LLM involved.
- **Response:**  
  `{ "tool_id", "name", "description", "configuration": { "mcpServers": { ... } }, "tools": [ { "name", "description", "input_schema" } ], "resources": [ ... ], "prompts": [ ... ] }`. The `configuration` object is the same MCP config as stored (passed as-is).
- **Errors:** 404 (tool not in catalog), 502 (MCP server failed to start or respond), 504 (timeout). Log all errors to stderr.

### 4.4 Run Tool

- **Method/Path:** `POST /api/v1/tools/run`
- **Body:**
  ```json
  {
    "tool_id": "naabu-mcp_...",
    "tool_name": "scan_ports",
    "arguments": {
      "target": "example.com",
      "ports": "80,443"
    }
  }
  ```
  - `tool_id`: From catalog.  
  - `tool_name`: MCP tool name (e.g. from get_tool_info).  
  - `arguments`: JSON object of parameter names and values.

- **Behavior:**
  1. **Check if tool is available** (in catalog and, if required, ensure environment is ready). If not → call **get_tool_info** flow to pull Docker image or ensure npx/uvx tool is available, then proceed.
  2. **Execute the tool** via MCP client: connect to the server (Docker/npx/uvx), call **call_tool(tool_name, arguments)** directly with the provided parameters. **No LLM.** Timeout configurable (e.g. env `TOOL_RUN_TIMEOUT_SECONDS`).
  3. **Normalize the result** into **OCSF format** (see §5).
  4. Return the OCSF JSON and appropriate HTTP status (200 on success; 4xx/5xx on validation or execution failure).

- **Response (success):** HTTP 200, body = **OCSF event/finding** (JSON). See §5.
- **Errors:** 400 (missing/invalid params), 404 (tool not found), 502 (tool execution failed), 504 (timeout). Log to stdout/stderr with structured fields (tool_id, tool_name, error type).

---

## 5. OCSF (Open Cybersecurity Schema Framework)

### 5.1 Why OCSF

- **Standardized** security/observability schema for events and findings.
- Vendor-agnostic, JSON-based, with a clear taxonomy (categories, class_uid, activity_id, etc.).
- Enables consistent ingestion by SIEMs, Security Lake, and analytics pipelines.

### 5.2 Research Summary

- **Spec:** [Open Cybersecurity Schema Framework](https://ocsf.io/). Schema browser: [schema.ocsf.io](https://schema.ocsf.io/).
- **Event model:** Events have `metadata`, `category_uid`, `class_uid`, `activity_id`, `time`, plus class-specific attributes (e.g. API Activity 6003, Detection Finding 2004).
- **Python libraries (use one, do not reinvent):**
  - **ocsf-lib** ([PyPI](https://pypi.org/project/ocsf-lib/)): Schema loading, API client, comparison. Python 3.11+.
  - **py-ocsf-models** ([PyPI](https://pypi.org/project/py-ocsf-models/)): Pydantic models for OCSF events/findings; good for serialization and validation. Python 3.9.1+.

### 5.3 Mapping Tool Execution to OCSF

- **Recommended class:** **API Activity (6003)** or **Detection Finding (2004)**.
  - **API Activity:** Fits “tool invoked via API” (this webservice is an API); use for generic “tool run” events.
  - **Detection Finding:** Fits when the tool output is a security finding/scan result (e.g. port scan, CVE check). Use when the tool’s output is clearly a finding.
- **Required/Recommended attributes (high level):**
  - `metadata` (product, version, correlation_uid).
  - `category_uid`, `class_uid`, `activity_id` (e.g. Read for “tool executed”).
  - `time`, `start_time`, `end_time`.
  - `actor` (e.g. service/caller identity).
  - `resources` or `raw_data`: put **tool name**, **tool_id**, **input arguments**, and **tool output** (text or structured) here or in `unmapped` / `raw_data` so the actual result is preserved.
- **Implementation:** Use **py-ocsf-models** or **ocsf-lib** to build the event object and serialize to JSON. Map:
  - Tool name / tool_id → resource details or unmapped.
  - Input `arguments` → unmapped or resource.
  - MCP `CallToolResult` content → `raw_data` or a structured field; keep full tool output available for downstream.

---

## 6. MCP Client & Tool Execution

### 6.1 Client Choice

- Use **FastMCP Python client** ([FastMCP – Calling Tools](https://gofastmcp.com/clients/tools)) or the **official MCP Python SDK** ([modelcontextprotocol](https://github.com/modelcontextprotocol)) with **stdio** transport.
- For **stdio:** Create `StdioServerParameters` (or equivalent) with `command`, `args`, `env` from the tool’s `mcp_server` config. Spawn process (or connect to existing container) and communicate over stdin/stdout.

### 6.2 Execution Flow

1. **Resolve config** from catalog cache by `tool_id`. Read the server entry from `tool.configuration.mcpServers` (one server per tool, or first key when multiple).
2. **Docker:** If that server’s `command === "docker"`, ensure image exists (`docker pull` if not), then `docker run ...` with `args` and `env`. Connect MCP client to the container’s stdio (e.g. attach to process or use `docker run -i` and stream stdin/stdout).
3. **npx:** Run `npx` with that server’s `args` in the webservice container (Node.js and npx installed in image). MCP client uses stdio to that process.
4. **uvx:** Run `uvx` with that server’s `args` in the webservice container (uv installed in image). MCP client uses stdio to that process.
5. **call_tool(name, arguments)** with the given `tool_name` and `arguments`; collect result.
6. Map result to OCSF and return.

### 6.3 Timeouts & Errors

- Enforce **timeouts** for pull, start, and call_tool (env-driven). On timeout or crash: log, return 504 or 502 with clear message; optionally still emit an OCSF event with status “failure”.

---

## 7. Docker & Runtime

### 7.1 Webservice Dockerfile

- **Base:** Python 3.11+ (or 3.12) slim image for compatibility with ocsf-lib / py-ocsf-models and FastMCP.
- **Install:**
  - Application deps: FastAPI, uvicorn, boto3, cachetools, ocsf-lib or py-ocsf-models, MCP client (FastMCP or mcp).
  - **Docker CLI** (for running tool containers): install Docker CLI and mount Docker socket (`/var/run/docker.sock`) or use DinD sidecar.
  - **Node.js** (for npx tools): install Node.js LTS in the image so `npx` is available.
  - **uv** (for uvx tools): install uv and ensure `uvx` is on PATH.
- **Multi-arch:** Build for `linux/amd64` and `linux/arm64` so it runs on Mac (ARM/Intel) and Linux (ARM/AMD). Use buildx and stage that supports both (slim images usually have both).
- **User:** Run as non-root where possible; document socket/permissions for Docker access.
- **Logging:** All application logs to **stdout** and **stderr** (no file logging by default); use structured logging (e.g. JSON with level, message, tool_id, request_id).

### 7.2 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TOOLS_CATALOG_S3_URI` or `TOOLS_CATALOG_URL` | S3 URI or URL to tools catalog JSON | `s3://bucket/tools/catalog.json` |
| `TOOLS_CACHE_TTL_SECONDS` | TTL for in-memory tools cache | `300` |
| `TOOL_RUN_TIMEOUT_SECONDS` | Timeout for a single tool run | `120` |
| `AWS_REGION` / AWS credentials | For S3 access if using S3 URI | |
| `LOG_LEVEL` | Logging level | `INFO` |

### 7.3 Docker Compose / Run

- Mount Docker socket: `-v /var/run/docker.sock:/var/run/docker.sock` (or use DinD service).
- Pass env vars for catalog URL and TTL. Ensure network allows pull from Docker Hub (and optional private registries).

---

## 8. Exceptions & Logging

### 8.1 Exceptions

- Define **custom exceptions** where useful (e.g. `ToolNotFoundError`, `ToolExecutionError`, `CatalogLoadError`). Map to HTTP status: 404, 502, 503, 504.
- Catch at boundary and return consistent **JSON error body**: `{ "error": "code", "message": "human message", "details": {} }`.
- Never leak internal paths or credentials in responses; log full context to stderr.

### 8.2 Logging

- **stdout:** Request access, success responses (optional, or summary only).
- **stderr:** Errors, catalog load failures, tool execution failures, timeouts, stack traces (at DEBUG).
- **Structured fields:** `request_id`, `tool_id`, `tool_name`, `duration_ms`, `status`. Use a standard logging library (e.g. `structlog` or `logging` with JSON formatter).

---

## 9. Quality & Compliance

- **Input validation:** Validate `tool_id`, `tool_name`, `arguments` (types and required fields from tool schema when available). Return 400 with clear messages.
- **Idempotency:** GET endpoints idempotent; POST run_tool is not (each call runs the tool).
- **Security:** Do not log or return secrets (env vars like AWS keys); mask in logs. Run containers with least privilege where possible.
- **CORS:** Configure CORS if the API is called from browsers.
- **Health:** `GET /health` or `GET /ready` that checks cache loaded and optionally Docker connectivity.

---

## 10. Out of Scope (Explicit)

- **No LLM:** The service does not call any LLM; it only invokes MCP tools with given parameters.
- **No custom cache implementation:** Use cachetools (or similar). No custom TTL logic.
- **No custom OCSF implementation:** Use ocsf-lib or py-ocsf-models.
- **No auth in PRD:** Auth (API keys, IAM, etc.) can be added in a later iteration; not required for this PRD.

---

## 11. Deliverables Checklist

- [ ] **S3/URL tools catalog:** JSON format documented and (optional) migration script from CSV.
- [ ] **FastAPI app:** Endpoints list, search, get_tool_info, run_tool; env-based config; caching with cachetools.
- [ ] **MCP client integration:** Stdio client; support docker, npx, uvx; pull image if missing; get_tool_info returns tools/resources/prompts.
- [ ] **OCSF response:** run_tool returns OCSF JSON using py-ocsf-models or ocsf-lib; mapping doc or comments in code.
- [ ] **Dockerfile:** Multi-arch (amd64/arm64), Python + Docker CLI + Node.js + uv; logging to stdout/stderr.
- [ ] **Exceptions & logging:** Custom exceptions, HTTP mapping, structured logging.
- [ ] **Tests:** Unit tests for cache, parsing, OCSF mapping; integration tests for at least one Docker and one npx/uvx tool if feasible.
- [ ] **README:** How to run (env vars, docker run example), API summary, OCSF reference.

---

## 12. References

- [OCSF](https://ocsf.io/), [schema.ocsf.io](https://schema.ocsf.io/), [ocsf-lib PyPI](https://pypi.org/project/ocsf-lib/), [py-ocsf-models PyPI](https://pypi.org/project/py-ocsf-models/).
- [FastMCP – Clients & Calling Tools](https://gofastmcp.com/clients/tools), [MCP Python SDK](https://github.com/modelcontextprotocol).
- [cachetools](https://cachetools.readthedocs.io/).
- Current tools CSV: `webservice/2026-03-07T20-14_export.csv`; example MCP config: `naabu-mcp/mcpServer.json`, README: repo root `README.md`.
