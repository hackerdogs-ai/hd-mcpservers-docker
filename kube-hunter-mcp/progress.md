# Kube-Hunter MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`kube-hunter-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping kube-hunter CLI
  - [x] `run_kube_hunter` tool — run kube-hunter with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add kube-hunter install steps to `Dockerfile` (see [aquasecurity/kube-hunter](https://github.com/aquasecurity/kube-hunter))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8252
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8252** — Kube-Hunter MCP Server (streamable-http)

## Notes

- Source: https://github.com/aquasecurity/kube-hunter
- Binary: `kube-hunter`
- Install: see https://github.com/aquasecurity/kube-hunter for installation instructions
