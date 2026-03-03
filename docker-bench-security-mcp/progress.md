# Docker Bench Security MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`docker-bench-security-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping docker-bench-security.sh CLI
  - [x] `run_docker_bench_security` tool — run docker-bench-security.sh with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add docker-bench-security.sh install steps to `Dockerfile` (see [docker/docker-bench-security](https://github.com/docker/docker-bench-security))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8254
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8254** — Docker Bench Security MCP Server (streamable-http)

## Notes

- Source: https://github.com/docker/docker-bench-security
- Binary: `docker-bench-security.sh`
- Install: see https://github.com/docker/docker-bench-security for installation instructions
