# Phase 2 — First 5 (alphabetical by mcp_server_name)

First five Phase 2 (COPY_DOCKER_CONFIG) servers added alphabetically:

| # | mcp_server_name | Tool (audit) | Upstream image | Port (if HTTP) |
|---|-----------------|--------------|----------------|----------------|
| 1 | **acuvity-mcp-server-alterx-mcp** | Alterx MCP | acuvity/mcp-server-alterx | 8380 |
| 2 | **acuvity-mcp-server-amass-mcp** | Amass MCP Server | acuvity/mcp-server-amass | 8381 |
| 3 | **acuvity-mcp-server-arjun-mcp** | Arjun MCP Server | acuvity/mcp-server-arjun | 8382 |
| 4 | **acuvity-mcp-server-assetfinder-mcp** | Assetfinder MCP Server | acuvity/mcp-server-assetfinder | 8383 |
| 5 | **acuvity-mcp-server-atlas-docs-mcp** | Atlas Docs MCP Server | acuvity/mcp-server-atlas-docs | 8384 |

Each has:
- `README.md` — Hackerdogs logo, description, Docker run (stdio), env/port note, upstream links
- `mcpServer.json` — Claude/Cursor config using upstream image (`docker run -i --rm <image>:latest`)
- `progress.md` — Phase 2 checklist

**Next:** Add to root README tool table when ready; optionally add Dockerfile/test.sh for full §2 compliance.
