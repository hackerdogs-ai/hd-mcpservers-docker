# Evil-WinRM MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`evil-winrm-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping evil-winrm CLI
  - [x] `run_evil_winrm` tool — run evil-winrm with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [ ] Add evil-winrm install steps to `Dockerfile` (see [Hackplayers/evil-winrm](https://github.com/Hackplayers/evil-winrm))
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8263
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8263** — Evil-WinRM MCP Server (streamable-http)

## Notes

- Source: https://github.com/Hackplayers/evil-winrm
- Binary: `evil-winrm`
- Install: see https://github.com/Hackplayers/evil-winrm for installation instructions
