<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Adblock MCP Server

MCP server that checks URLs against AdBlock Plus compatible blocklists (EasyList).

**Tools:**
| Tool | Description |
|------|-------------|
| `adblock_check_url` | Check if a URL would be blocked by AdBlock Plus rules |

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/adblock-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8508:8508 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8508 \
  hackerdogs/adblock-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8508/mcp` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8508` |

## Example prompts

- "Check if https://ads.example.com/banner.js is blocked by EasyList."
- "Is this URL on the adblock blocklist?"
