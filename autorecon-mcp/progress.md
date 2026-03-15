# AutoRecon MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`autorecon-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping autorecon CLI
  - [x] `run_autorecon` tool — run autorecon with arguments
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
  - [x] JSON output parsing
- [x] Add autorecon install steps to `Dockerfile` — **robust image**: Kali base + full tool stack (nmap, nikto, feroxbuster, gobuster, seclists, etc.), venv with AutoRecon; MCP server runs autorecon with PTY for non-interactive use
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8201
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable

## Port Assignment

- **8201** — AutoRecon MCP Server (streamable-http)

## Notes

- Source: https://github.com/Tib3rius/AutoRecon
- Binary: `autorecon`
- Install: in Dockerfile, `pip install git+https://github.com/Tib3rius/AutoRecon.git`
