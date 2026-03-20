<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Name Server MCP Server

MCP server to check if IPs are known public DNS resolvers (Google, Cloudflare, Quad9, OpenDNS, AdGuard).

**Tools:**
- `nameserver_check_ip` — Check if an IP is a known public DNS resolver

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/name-server-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8525:8525 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8525 \
  hackerdogs/name-server-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.  
**HTTP:** Connect to `http://localhost:8525` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8525` |

## Example prompts

- "Is 8.8.8.8 a public DNS resolver?"
- "Check if 1.1.1.1 is a known nameserver."
- "What provider runs the DNS resolver at 9.9.9.9?"
