# Tools Web Service — Step-by-Step Guide

This guide walks through: **Install**, **Run locally**, **Test**, **Build & publish Docker**, and **Test with Docker**.

Use the **webservice `test.sh`** in this directory to test the API (see [§3 Test](#3-test) and [§5 Test with Docker](#5-test-with-docker)).

---

## 1. Install

All steps assume you are in the repo root or the `webservice` directory as indicated.

### 1.1 Clone and enter webservice

```bash
cd /path/to/hd-mcpservers-docker/webservice
```

### 1.2 Python virtual environment and dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 1.3 (Optional) Environment file for local catalog

```bash
cp .env.example .env
# Edit .env and set TOOLS_CATALOG_URL (see step 2.1 if using a file catalog)
```

---

## 2. Run the service locally and execute

### 2.1 Create a local catalog (one-time)

Generate `catalog.json` from the tools export CSV so the API can load tools without S3/HTTPS:

```bash
cd webservice
python scripts/csv_to_catalog.py
# Creates catalog.json in the same directory
```

To use this file, either:

- Let `start_local.sh` auto-detect it (see 2.2), or  
- In `.env` set (use your **absolute** path, three slashes after `file:`):

  ```env
  TOOLS_CATALOG_URL=file:///Users/you/hd-mcpservers-docker/webservice/catalog.json
  ```

### 2.2 Start the API (no Docker)

**Option A — start script (recommended)**

```bash
cd webservice
./start_local.sh
```

- Uses `.venv` if present.  
- If `TOOLS_CATALOG_URL` and `TOOLS_CATALOG_S3_URI` are unset and `catalog.json` exists, sets the catalog to `file://$(pwd)/catalog.json`.  
- Listens on port **8000** by default.

**Option B — manual**

```bash
cd webservice
source .venv/bin/activate
export TOOLS_CATALOG_URL="file://$(pwd)/catalog.json"   # if you have catalog.json
python run.py
```

**Different port**

```bash
PORT=8001 ./start_local.sh
# or
PORT=8001 python run.py
```

### 2.3 Endpoints

With the service running:

| What        | URL |
|------------|-----|
| API base   | http://localhost:8000 |
| Health     | http://localhost:8000/health |
| Ready      | http://localhost:8000/ready |
| API docs   | http://localhost:8000/docs |
| List tools | http://localhost:8000/api/v1/tools |
| Search     | http://localhost:8000/api/v1/tools/search?q=... |
| Tool info  | http://localhost:8000/api/v1/tools/{tool_id} |
| Run tool   | POST http://localhost:8000/api/v1/tools/run |

---

## 3. Test

Use the **webservice `test.sh`** script. It assumes the API is **already running** (from step 2).

### 3.1 Run tests (API must be running)

In a **second terminal** (keep the API running in the first):

```bash
cd webservice
./test.sh
```

Default base URL is `http://localhost:8000`. To test another host/port:

```bash
./test.sh http://localhost:8000
./test.sh http://localhost:8080
```

### 3.2 What test.sh does

- **Test 1:** `GET /health` — expects 200 and a `status` field.  
- **Test 2:** `GET /ready` — expects 200 (or 503 if catalog is not configured).  
- **Test 3:** `GET /api/v1/tools` — expects 200 and a `tools` array (or 503 if no catalog).  
- **Test 4:** `GET /api/v1/tools/search?q=naabu` — expects 200 and a `tools` array (or 503).  
- **Test 5:** `GET /docs` — expects 200.

If the catalog is not set, 503 on ready/list/search is treated as **pass** so the script still validates that the service is up and responding.

### 3.3 Which test.sh to use

Use **`webservice/test.sh`** (this directory). It is the test script for the **Tools Web Service API**.

The other `test.sh` files in the repo (e.g. `naabu-mcp/test.sh`, `wfuzz-mcp/test.sh`) are for **individual MCP server images** (Docker + MCP protocol). They are **not** for the webservice; use them when testing those MCP tools in isolation.

---

## 4. Create and publish Docker image

### 4.1 Build only (local image)

```bash
cd webservice
./publish_to_hackerdogs.sh --build hackerdogs
```

- Builds the image for your current platform.  
- Tags: `tools-webservice:latest` and `hackerdogs/tools-webservice:latest`.  
- Does **not** push to Docker Hub.

### 4.2 Build and publish to Docker Hub

```bash
cd webservice
./publish_to_hackerdogs.sh hackerdogs
```

- Builds for **linux/amd64** and **linux/arm64** (multi-arch).  
- Pushes to `hackerdogs/tools-webservice:latest`.  
- Requires `docker login` when publishing.

### 4.3 Other options

```bash
./publish_to_hackerdogs.sh --help
```

Examples:

- Publish with a version tag:  
  `./publish_to_hackerdogs.sh hackerdogs v1.0.0 latest`
- Build and publish one platform at a time:  
  `./publish_to_hackerdogs.sh --platforms sequential hackerdogs`
- Publish only (image already built):  
  `./publish_to_hackerdogs.sh --publish hackerdogs latest`

### 4.4 Version log

The script appends a line to `tools-webservice_versions.txt` (tags, platforms, timestamp, Docker Hub link).

---

## 5. Test with Docker

### 5.1 Run the container

Catalog must be provided via environment variable. Example with a **file** catalog: mount the file and point the app at it with a file URL (the app reads via HTTP, so use a URL that works inside the container). Easiest is to use an **HTTPS** or **S3** catalog in production. For local Docker testing you can:

**Option A — mount catalog and use file URL inside container**

```bash
cd webservice
# Ensure catalog.json exists (python scripts/csv_to_catalog.py)
docker run --rm -p 8000:8000 \
  -v "$(pwd)/catalog.json:/app/catalog.json:ro" \
  -e TOOLS_CATALOG_URL=file:///app/catalog.json \
  -e TOOL_RUN_TIMEOUT_SECONDS=120 \
  hackerdogs/tools-webservice:latest
```

**Option B — use S3 or HTTPS**

```bash
docker run --rm -p 8000:8000 \
  -e TOOLS_CATALOG_URL=https://example.com/catalog.json \
  hackerdogs/tools-webservice:latest
```

If tools that run as Docker containers need to be executed, mount the Docker socket:

```bash
docker run --rm -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$(pwd)/catalog.json:/app/catalog.json:ro" \
  -e TOOLS_CATALOG_URL=file:///app/catalog.json \
  hackerdogs/tools-webservice:latest
```

### 5.2 Run the same test script against the container

With the container running on port 8000:

```bash
cd webservice
./test.sh http://localhost:8000
```

If the container is on another port:

```bash
./test.sh http://localhost:8080
```

Use **the same `webservice/test.sh`** for both local and Docker; only the base URL changes.

---

## Quick reference

| Step            | Command / action |
|-----------------|------------------|
| Install         | `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` |
| Catalog         | `python scripts/csv_to_catalog.py` |
| Run locally     | `./start_local.sh` |
| Test (API up)   | `./test.sh` or `./test.sh http://localhost:8000` |
| Build image     | `./publish_to_hackerdogs.sh --build hackerdogs` |
| Publish image   | `./publish_to_hackerdogs.sh hackerdogs` |
| Run Docker      | `docker run --rm -p 8000:8000 -e TOOLS_CATALOG_URL=file:///app/catalog.json -v "$(pwd)/catalog.json:/app/catalog.json:ro" hackerdogs/tools-webservice:latest` |
| Test with Docker| `./test.sh http://localhost:8000` |

**Which test.sh:** Use **`webservice/test.sh`** for the Tools Web Service API. Do not use the per–MCP-server `test.sh` scripts (e.g. `naabu-mcp/test.sh`) for the webservice.
