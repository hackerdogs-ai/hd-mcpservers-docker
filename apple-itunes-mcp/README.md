<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Apple iTunes MCP Server

MCP server that searches Apple iTunes for apps associated with a domain.

**Tools:**
| Tool | Description |
|------|-------------|
| `itunes_search_apps` | Search iTunes for apps whose bundle ID matches a domain |

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/apple-itunes-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8511:8511 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8511 \
  hackerdogs/apple-itunes-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8511/mcp` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8511` |

## Example prompts

- "Find iOS apps associated with google.com."
- "Search iTunes for apps by example.com."
