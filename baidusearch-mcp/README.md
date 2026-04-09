<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Baidu Search MCP Server

MCP server that searches Baidu and extracts emails and hostnames from results.

**Tools:**
| Tool | Description |
|------|-------------|
| `baidu_search` | Search Baidu and extract emails and hostnames from results |

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/baidusearch-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8514:8514 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8514 \
  hackerdogs/baidusearch-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.
**HTTP:** Connect to `http://localhost:8514/mcp` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8514` |

## Example prompts

- "Search Baidu for emails and hostnames related to example.com."
- "Extract contact info from Baidu search results for this query."
