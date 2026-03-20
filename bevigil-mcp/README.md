<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# BeVigil MCP Server

MCP server for [BeVigil](https://bevigil.com) mobile app OSINT — discover subdomains and URLs from mobile app analysis.

**Requires:** `BEVIGIL_API_KEY` (get a key at [bevigil.com](https://bevigil.com)).

**Tools:**
- `bevigil_domain_osint` — Get subdomains and URLs for a domain from BeVigil mobile app OSINT

## Deploy

### Docker Compose
```bash
docker-compose up -d
```
Set `BEVIGIL_API_KEY` in the environment or a `.env` file.

### Docker Run (stdio)
```bash
docker run -i --rm -e BEVIGIL_API_KEY=your_key hackerdogs/bevigil-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8515:8515 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8515 \
  -e BEVIGIL_API_KEY=your_key \
  hackerdogs/bevigil-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`; set `BEVIGIL_API_KEY` in `env`.
**HTTP:** Connect to `http://localhost:8515` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8515` |
| `BEVIGIL_API_KEY` | BeVigil API key | required |

## Example prompts

- "Get subdomains for example.com using BeVigil."
- "Find URLs associated with hackerdogs.ai from mobile apps."
