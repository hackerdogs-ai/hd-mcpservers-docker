<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Archive.org MCP Server

MCP server that queries the Wayback Machine for archived snapshots of URLs.

**Tools:**
| Tool | Description |
|------|-------------|
| `wayback_lookup` | Check if a URL has Wayback Machine snapshots |

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/archiveorg-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8512:8512 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8512 \
  hackerdogs/archiveorg-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8512/mcp` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8512` |

## Example prompts

- "Check if https://example.com has Wayback Machine snapshots."
- "Look up archive.org history for this URL."
