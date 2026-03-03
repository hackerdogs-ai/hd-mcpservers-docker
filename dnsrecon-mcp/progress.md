# DNSRecon MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`dnsrecon-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping dnsrecon CLI
  - [x] `run_dnsrecon` tool — run dnsrecon with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add dnsrecon install steps to `Dockerfile` (see [darkoperator/dnsrecon](https://github.com/darkoperator/dnsrecon))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8203
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8203** — DNSRecon MCP Server (streamable-http)

## Notes

- Source: https://github.com/darkoperator/dnsrecon
- Binary: `dnsrecon`
- Install: see https://github.com/darkoperator/dnsrecon for installation instructions
