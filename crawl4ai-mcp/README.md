<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Crawl4AI MCP Server

MCP server for AI-powered web crawling via [Crawl4AI](https://github.com/unclecode/crawl4ai).

**Requires:** A running Crawl4AI instance (default: `http://localhost:11235`).

**Tools:**
- `crawl4ai_crawl` — Crawl a URL with optional CSS selector and screenshot

## Deploy

### Docker Compose
```bash
docker-compose up -d
```
Set `CRAWL4AI_URL` and `CRAWL4AI_API_TOKEN` in the environment or a `.env` file.

### Docker Run (stdio)
```bash
docker run -i --rm -e CRAWL4AI_URL=http://host.docker.internal:11235 hackerdogs/crawl4ai-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8521:8521 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8521 \
  -e CRAWL4AI_URL=http://host.docker.internal:11235 \
  hackerdogs/crawl4ai-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`; set `CRAWL4AI_URL` and `CRAWL4AI_API_TOKEN` in `env`.  
**HTTP:** Connect to `http://localhost:8521` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8521` |
| `CRAWL4AI_URL` | Crawl4AI API URL | `http://localhost:11235` |
| `CRAWL4AI_API_TOKEN` | Crawl4AI API token | (empty) |

## Example prompts

- "Crawl https://example.com and extract the content."
- "Scrape the main article from https://news.ycombinator.com using CSS selector .titleline."
