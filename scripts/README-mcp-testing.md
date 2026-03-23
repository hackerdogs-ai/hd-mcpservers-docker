# MCP server testing (`test.sh`)

Each MCP server directory should include a **`test.sh`** that proves the image works end-to-end.

## Standard flow (6 steps)

Shared implementation: **`mcp-standard-six-test.sh`**

1. **Install** — `docker build -t <image> <mcp-directory>`
2. **stdio** — `tools/list` after `initialize` + `notifications/initialized`
3. **stdio** — `tools/call` for one real tool (name + arguments you choose)
4. **HTTP streamable** — same sequence against `http://localhost:<port>/mcp`
5. **HTTP streamable** — `tools/call` for the same tool (new JSON-RPC `id`)
6. **Tear down** — `docker stop` / `docker rm` the HTTP test container

## Per-server `test.sh` (thin wrapper)

Set exports, then `exec` the standard script:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_SCRIPTS="$(cd "$SCRIPT_DIR/../scripts" && pwd)"

export MCP_PROJECT_DIR="$SCRIPT_DIR"
export MCP_IMAGE="your-image-name"
export MCP_PORT=8600
export MCP_CONTAINER="your-image-test"
export MCP_TOOL_NAME="tool_name"
export MCP_TOOL_ARGUMENTS='{"arg":"value"}'   # JSON object only
export MCP_EXTRA_DOCKER_ARGS=""               # optional, e.g. -e AWS_REGION=us-east-1 ...

exec bash "$REPO_SCRIPTS/mcp-standard-six-test.sh"
```

Reference: **`ai-humanizer-mcp/test.sh`**.

## Evidence file

After each run, **`test-results.txt`** is written in the MCP server directory (`MCP_PROJECT_DIR`). It includes **raw outputs** for every step (docker build log, stdio JSON-RPC lines, HTTP headers/bodies, `tools/call` payloads), not only PASS/FAIL.

To disable truncation of huge blobs, set `MCP_TEST_RESULT_MAX_CHARS=0` before running.

## Credentials

Pass secrets only via **`MCP_EXTRA_DOCKER_ARGS`** (or extend the standard script to support `--env-file`). Do not commit real keys; CI/local can inject them when running `./test.sh`.

## `mcp_http_proxy.py` (stdio → HTTP)

Canonical implementation: **`scripts/mcp_http_proxy.py`**.

- **Drains the child process stderr** so Java/Node MCP servers cannot deadlock when they log heavily.
- **Long timeouts** (default **120s** initialize, **240s** per request); override with `MCP_PROXY_INIT_TIMEOUT` / `MCP_PROXY_REQUEST_TIMEOUT`.

After editing the canonical file, sync into every server copy:

```bash
SRC=scripts/mcp_http_proxy.py
find . -name mcp_http_proxy.py -type f ! -path "./$SRC" -exec cp "$SRC" {} \;
```

Then **rebuild** affected Docker images so the new proxy is in the image.

### Rebuild all fixed images (proxy + `hd_fetch`)

After syncing `mcp_http_proxy.py` or changing the four `hd_fetch` Dockerfiles, rebuild **79** images in one pass (uses each `test.sh` `IMAGE=…` tag when set):

```bash
./scripts/rebuild-fixed-images.sh
# log defaults to ./rebuild-fixed-images.log at repo root
# or:  LOG=/path/to.log ./scripts/rebuild-fixed-images.sh
```

Resume after a failure (sorted basenames):

```bash
START_AFTER=aws-network-mcp ./scripts/rebuild-fixed-images.sh
```

Smoke (first 3 builds only):

```bash
MAX_BUILDS=3 ./scripts/rebuild-fixed-images.sh
```

Full run can take **hours**; use `tail -f rebuild-fixed-images.log`.

### Verify rebuilt images (79 `test.sh` runs)

After a rebuild, run tests only for those same directories:

```bash
./scripts/verify-rebuilt-images.sh
# writes verify-rebuilt-79.log and prints a PASS/FAIL summary
```

Options: `MAX_TESTS=N`, `START_AFTER=dirname`, `VERIFY_LOG=/path/to.log`.

## Run every server (`run-all-mcp-tests.sh`)

From the repo root:

```bash
./scripts/run-all-mcp-tests.sh
```

- Discovers every **`*/test.sh`** (386+ MCP directories).
- **Structured `test-results.txt`** is left to servers that already use **`mcp-standard-six-test.sh`** or define **`append_section`** (e.g. `ai-infra-guard-mcp`).
- **All other servers** get **`test-results.txt`** filled with a **full stdout/stderr capture** of their `./test.sh`.
- Writes **`ALL_MCP_TESTS_SUMMARY.tsv`** and **`ALL_MCP_TESTS_RUN.log`** at the repo root.

Smoke a subset:

```bash
RUN_MAX=10 ./scripts/run-all-mcp-tests.sh
```

Resume partway through the sorted list (1-based index):

```bash
RUN_START=200 RUN_MAX=50 ./scripts/run-all-mcp-tests.sh
```

Full sweep can take **many hours** (Docker builds). For a long run:

```bash
nohup env RUN_MAX= ./scripts/run-all-mcp-tests.sh >> run-all-tests.nohup.out 2>&1 &
```
