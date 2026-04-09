<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# CertGraph MCP Server

MCP server for [CertGraph](https://github.com/lanrat/certgraph) — build certificate transparency relationship graphs for domains.

**Tools:**
- `certgraph_scan` — Build a certificate graph for a host (with configurable depth and timeout)

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/certgraph-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8519:8519 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8519 \
  hackerdogs/certgraph-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8519` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8519` |

## Example prompts

- "Build a certificate graph for example.com."
- "Map the certificate relationships for hackerdogs.ai with depth 2."
