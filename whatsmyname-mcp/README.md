<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# WhatsMyName MCP Server

MCP server for [WhatsMyName](https://github.com/WebBreacher/WhatsMyName) — username enumeration across websites.

**Tools:**
- `whatsmyname_check` — Check if a username exists on various sites

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/whatsmyname-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8528:8528 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8528 \
  hackerdogs/whatsmyname-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8528` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8528` |

## Example prompts

- "Check if username 'johndoe' exists on social media sites."
- "Enumerate username 'hackerdogs' across the top 100 sites."
