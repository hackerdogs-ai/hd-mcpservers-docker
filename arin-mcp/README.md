<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# ARIN MCP Server

MCP server that queries the ARIN Whois REST API for IP and organization information.

**Tools:**
| Tool | Description |
|------|-------------|
| `arin_lookup` | Look up an IP address or organization in ARIN Whois |

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/arin-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8513:8513 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8513 \
  hackerdogs/arin-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8513/mcp` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8513` |

## Example prompts

- "Look up ARIN whois for 8.8.8.8."
- "Get ARIN organization info for GOOGL."
