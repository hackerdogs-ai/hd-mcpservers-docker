<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Bitbucket MCP Server

MCP server for [Bitbucket](https://bitbucket.org) code search — extract emails and hostnames from public code.

**Tools:**
- `bitbucket_code_search` — Search Bitbucket code and extract emails/hostnames

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/bitbucket-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8516:8516 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8516 \
  hackerdogs/bitbucket-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8516` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8516` |

## Example prompts

- "Search Bitbucket code for example.com."
- "Find emails in public Bitbucket repos mentioning hackerdogs."
