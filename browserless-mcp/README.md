<p align="center">
  <a href="https://hackerdogs.ai"><img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/></a>
  <br/>
  <a href="https://hackerdogs.ai"><img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/></a>
</p>

# Browserless MCP Server

MCP server for headless Chrome via the [Browserless](https://www.browserless.io/) API — content extraction, screenshots, PDFs, and scraping.

**Requires:** A running Browserless instance (default: `http://localhost:3000`).

**Tools:**
- `browserless_content` — Get rendered HTML content from a URL
- `browserless_screenshot` — Take a screenshot of a URL
- `browserless_pdf` — Generate PDF from a URL
- `browserless_scrape` — Scrape specific elements from a URL

## Deploy

### Docker Compose
```bash
docker-compose up -d
```
Set `BROWSERLESS_URL` and `BROWSERLESS_API_KEY` in the environment or a `.env` file.

### Docker Run (stdio)
```bash
docker run -i --rm -e BROWSERLESS_URL=http://host.docker.internal:3000 hackerdogs/browserless-mcp:latest
```

### Docker Run (HTTP streamable)
```bash
docker run -d -p 8518:8518 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8518 \
  -e BROWSERLESS_URL=http://host.docker.internal:3000 \
  hackerdogs/browserless-mcp:latest
```

## MCP Client Configuration

**Stdio:** Use `mcpServer.json`; set `BROWSERLESS_URL` and `BROWSERLESS_API_KEY` in `env`.  
**HTTP:** Connect to `http://localhost:8518` with `MCP_TRANSPORT=streamable-http`.

| Env | Description | Default |
|-----|-------------|---------|
| `MCP_TRANSPORT` | `stdio` or `streamable-http` | `stdio` |
| `MCP_PORT` | HTTP port (streamable-http) | `8518` |
| `BROWSERLESS_URL` | Browserless API URL | `http://localhost:3000` |
| `BROWSERLESS_API_KEY` | Browserless API key | (empty) |

## Example prompts

- "Get the rendered HTML content of https://example.com."
- "Take a full-page screenshot of https://news.ycombinator.com."
- "Generate a PDF of https://example.com."
- "Scrape the h1 elements from https://example.com."
