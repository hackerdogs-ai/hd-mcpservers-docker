<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Brave Search MCP Server

MCP server for [Brave Search](https://search.brave.com) — web search via the Brave Search API.

**Requires:** `BRAVE_API_KEY` (get a key at [brave.com/search/api](https://brave.com/search/api/)).

**Tools:**
- `brave_search` — Search the web using Brave Search API

## Deploy

### Docker Compose
```bash
docker-compose up -d
```
Set `BRAVE_API_KEY` in the environment or a `.env` file.

### Docker Run (stdio)
```bash
docker run -i --rm -e BRAVE_API_KEY=your_key hackerdogs/bravesearch-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8517:8517 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8517 \
  -e BRAVE_API_KEY=your_key \
  hackerdogs/bravesearch-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`; set `BRAVE_API_KEY` in `env`.
**HTTP:** Connect to `http://localhost:8517` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8517` |
| `BRAVE_API_KEY` | Brave Search API key | required |

## Example prompts

- "Search the web for 'latest cybersecurity vulnerabilities 2025'."
- "Find information about OSINT tools using Brave Search."
