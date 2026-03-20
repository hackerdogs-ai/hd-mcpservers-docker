<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# AdGuard DNS MCP Server

MCP server that checks if hosts are blocked by AdGuard DNS filtering.

**Tools:**
| Tool | Description |
|------|-------------|
| `adguard_dns_check` | Check if a host is blocked by AdGuard DNS (default, family, or both modes) |

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/adguard-dns-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8509:8509 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8509 \
  hackerdogs/adguard-dns-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8509/mcp` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8509` |

## Example prompts

- "Is example.com blocked by AdGuard DNS?"
- "Check if this host is filtered by AdGuard family protection."
