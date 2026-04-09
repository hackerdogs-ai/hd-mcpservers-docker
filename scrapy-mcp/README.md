<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Scrapy MCP Server

MCP server for web scraping via [Scrapy](https://scrapy.org/) spiders.

**Tools:**
- `scrapy_crawl` — Crawl a URL using Scrapy with configurable max pages

## Deploy

### Docker Compose
```bash
docker-compose up -d
```

### Docker Run (stdio)
```bash
docker run -i --rm hackerdogs/scrapy-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8526:8526 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8526 \
  hackerdogs/scrapy-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`.  
**HTTP:** Connect to `http://localhost:8526` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8526` |

## Example prompts

- "Scrape https://example.com using Scrapy."
- "Crawl https://news.ycombinator.com with max 5 pages."
