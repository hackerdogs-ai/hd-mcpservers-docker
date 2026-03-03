# Metasploit MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`metasploit-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping msfconsole CLI
  - [x] `run_metasploit` tool — run msfconsole with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add msfconsole install steps to `Dockerfile` (see [rapid7/metasploit-framework](https://github.com/rapid7/metasploit-framework))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8236
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8236** — Metasploit MCP Server (streamable-http)

## Notes

- Source: https://github.com/rapid7/metasploit-framework
- Binary: `msfconsole`
- Install: see https://github.com/rapid7/metasploit-framework for installation instructions
