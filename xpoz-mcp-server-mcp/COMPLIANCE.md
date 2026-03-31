# Batch 8 — five compliance criteria

This directory is the **reference** layout for Batch 8 remote-reference stubs: `Dockerfile`, `mcp_server.py`, `requirements.txt`, `docker-compose.yml`, and `test.sh` invoking the shared compliance runner.

Each `test.sh` must satisfy **all five** checks (implemented in `scripts/mcp-five-step-compliance.sh`).

| # | Criterion | What it verifies |
|---|-----------|------------------|
| 1 | **Docker image** | `hackerdogs/<server-dir>:latest` is available via `docker pull` or `docker build` from this folder. |
| 2 | **Stdio — tools/list** | Running the image with stdio transport returns a valid MCP `tools/list` response with tools. |
| 3 | **Stdio — tools/call** | A `tools/call` for the declared tool (e.g. `remote_endpoint_info`) returns `result`, `content`, or structured `error`. |
| 4 | **HTTP — tools/list** | With `MCP_TRANSPORT=streamable-http`, `POST /mcp` after `initialize` returns a tools list. |
| 5 | **HTTP — tools/call** | The same tool as in step 3 works over HTTP with the active session. |

**Run the full Batch 8 suite** (this server first, then seven peers):

```bash
bash scripts/run-batch8-tests.sh
```

Production MCP traffic for XPoz still uses the URL in `mcpServer.json` (`https://mcp.xpoz.io/mcp`); this image is for CI and protocol compliance only.
