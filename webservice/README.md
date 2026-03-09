# Tools Web Service

FastAPI service that serves an MCP tools catalog (from S3 or URL), with list, search, **get_tool_info**, and **run_tool** endpoints. Tool execution is direct (no LLM); results are returned in OCSF format. PRD: [PRD-ToolsWebService.md](./PRD-ToolsWebService.md).

## Features

- **Catalog:** Load tools from S3 or HTTPS URL; in-memory cache with configurable TTL (cachetools).
- **API:** `GET /api/v1/tools`, `GET /api/v1/tools/search?q=...`, `GET /api/v1/tools/{tool_id}`, `POST /api/v1/tools/run`.
- **MCP:** Connects to tools via stdio (docker, npx, uvx); lists tools/resources/prompts; runs tools with given arguments.
- **OCSF:** `run_tool` returns an OCSF API Activity (6003) event with tool output in `unmapped`.
- **Resiliency:** Global exception handlers; catalog load failure uses stale cache when possible; API does not crash.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TOOLS_CATALOG_S3_URI` | S3 URI to catalog JSON (`s3://bucket/key`) | — |
| `TOOLS_CATALOG_URL` | HTTPS URL to catalog JSON (if not using S3) | — |
| `TOOLS_CACHE_TTL_SECONDS` | Cache TTL in seconds | `300` |
| `TOOL_RUN_TIMEOUT_SECONDS` | Timeout for tool execution | `120` |
| `LOG_LEVEL` | Logging level | `INFO` |

AWS credentials (for S3) use default boto3 resolution (env, IAM, etc.).

## Testing without Docker

### 1. `.env` for the webservice

Copy `.env.example` to `.env` and set a catalog source.

**Local file (easiest for testing):** generate a catalog from the CSV, then point at it:

```bash
cd webservice
cp .env.example .env
# Generate catalog.json from the export CSV (run once)
python scripts/csv_to_catalog.py
# In .env set (use your actual absolute path; three slashes for file://):
# TOOLS_CATALOG_URL=file:///Users/you/path/to/hd-mcpservers-docker/webservice/catalog.json
```

Or use an HTTPS URL if you have a catalog hosted somewhere:

```env
TOOLS_CATALOG_URL=https://example.com/tools-catalog.json
```

Optional in `.env`:

```env
TOOLS_CACHE_TTL_SECONDS=300
TOOL_RUN_TIMEOUT_SECONDS=120
LOG_LEVEL=INFO
PORT=8000
```

### 2. Start the API (no Docker)

**Option A – script (uses `.venv` if present, auto-sets file catalog if `catalog.json` exists):**

```bash
cd webservice
python3 -m venv .venv && source .venv/bin/activate   # once
pip install -r requirements.txt                       # once
./start_local.sh
```

**Option B – manually:**

```bash
cd webservice
source .venv/bin/activate   # or skip if using system Python
export TOOLS_CATALOG_URL="file://$(pwd)/catalog.json"   # if you have catalog.json
python run.py
```

Then open:

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  
- Ready: http://localhost:8000/ready  

Different port: `PORT=8001 ./start_local.sh` or `PORT=8001 python run.py`.

## Run locally (generic)

```bash
cd webservice
pip install -r requirements.txt
export TOOLS_CATALOG_URL=https://example.com/catalog.json   # or TOOLS_CATALOG_S3_URI
python run.py
```

## Run with Docker

Build (multi-arch optional):

```bash
docker build -t tools-webservice .
```

Run (mount Docker socket for tool containers; pass catalog source):

```bash
docker run --rm -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e TOOLS_CATALOG_URL=https://example.com/catalog.json \
  tools-webservice
```

For S3, set AWS credentials or IAM:

```bash
docker run --rm -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e TOOLS_CATALOG_S3_URI=s3://your-bucket/catalog.json \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=... \
  -e AWS_SECRET_ACCESS_KEY=... \
  tools-webservice
```

Multi-arch build (Mac ARM/Intel, Linux ARM/AMD):

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t tools-webservice .
```

## Catalog JSON format

Catalog is a JSON object with a `tools` array. Each tool has `id`, `name`, `description`, `configuration` (passed as-is). `configuration` must be `{ "mcpServers": { "<server_name>": { "command", "args", "env" } } }`. See PRD §2.2.

## Logging and errors

- Logs go to **stdout** (INFO and below) and **stderr** (WARNING and above).
- All exceptions are caught and returned as JSON (4xx/5xx); no unhandled crashes.
- Errors include `error`, `message`, and `details` fields.
