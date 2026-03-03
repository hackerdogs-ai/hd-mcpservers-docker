# Kube-Bench MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`kube-bench-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping kube-bench CLI
  - [x] `run_kube_bench` tool — run kube-bench with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add kube-bench install steps to `Dockerfile` (see [aquasecurity/kube-bench](https://github.com/aquasecurity/kube-bench))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8253
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8253** — Kube-Bench MCP Server (streamable-http)

## Notes

- Source: https://github.com/aquasecurity/kube-bench
- Binary: `kube-bench`
- Install: see https://github.com/aquasecurity/kube-bench for installation instructions
