# Suricata MCP Server — Progress

## Setup Steps

- [x] Create directory structure (`suricata-mcp/`)
- [x] Create `requirements.txt` with fastmcp dependency
- [x] Create `mcp_server.py` with FastMCP server wrapping suricata CLI
  - [x] `run_suricata` tool — run suricata with arguments
  - [x] `analyze_pcap` tool — analyze PCAP files and return alerts/events
  - [x] Support stdio and streamable-http transports
  - [x] Robust error handling and timeouts
- [x] Create `Dockerfile` with Suricata IDS installation via apt
- [x] Create `publish_to_hackerdogs.sh` — build/publish script with multi-arch support
- [x] Create `mcpServer.json` — MCP server config for Claude/Cursor installation
- [x] Create `docker-compose.yml` — port 8365
- [x] Create `test.sh` — test suite for stdio and http transports
- [x] Create `README.md` — with Hackerdogs logo and full documentation
- [x] Create `progress.md` — this file
- [x] Make scripts executable
- [x] Build and test Docker image (6/6 tests pass)

## Port Assignment

- **8365** — Suricata MCP Server (streamable-http)

## Notes

- Source: https://suricata.io/ and https://github.com/OISF/suricata
- Binary: `suricata` (IDS/IPS engine installed via apt)
- Rules: Emerging Threats rules pre-loaded via `suricata-update`
- Original `Medinios/SuricataMCP` was itself an MCP server (not a CLI tool) — replaced with direct suricata binary wrapping
