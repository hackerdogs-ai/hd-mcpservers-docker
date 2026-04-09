# Abuse.ch MCP Server — Progress

## Setup Steps
- [x] requirements.txt (fastmcp, httpx)
- [x] mcp_server.py — FastMCP, urlhaus_host, urlhaus_url, malwarebazaar_hash, threatfox_iocs; stdio + streamable-http
- [x] Dockerfile (Python 3.11-slim, non-root, MCP_PORT=8373)
- [x] mcpServer.json, docker-compose.yml
- [x] test.sh — stdio + HTTP streamable tests
- [x] README.md, progress.md
- [x] publish_to_hackerdogs.sh (see template)

## Port
- **8373** — Abuse.ch MCP (streamable-http)
