<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Scrapy MCP Server

MCP server wrapper for [Scrapy](https://scrapy.org/) — programmatic web crawling and content extraction via Scrapy spiders.

## What is Scrapy?

Scrapy is the industry-standard Python web scraping and crawling framework, capable of following links across a site, extracting structured data from HTML, handling JavaScript-rendered pages via middleware, and managing request throttling and robots.txt compliance. See [scrapy/scrapy](https://github.com/scrapy/scrapy) for full documentation.

**No API keys required** — Scrapy runs locally inside the Docker container fetching public web pages directly.

**Tools:**
- `scrapy_crawl` — Crawl a URL using Scrapy and return a preview of the fetched page content.

## Tools Reference

### `scrapy_crawl`

Crawl a URL using Scrapy.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | str | Yes | — | Starting URL to fetch and crawl |
| `max_pages` | int | No | `10` | Maximum number of pages to follow |

<details>
<summary>Example response</summary>

```json
{
  "url": "https://example.com",
  "content_preview": "<!DOCTYPE html>...",
  "length": 1256
}
```

</details>

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Crawl https://docs.example.com and extract the text content of the first page."
- "Fetch https://news.ycombinator.com with Scrapy and show me the raw HTML of the front page."
- "Use Scrapy to download and preview the content of https://example.com/sitemap.xml."
- "Crawl this documentation site (up to 5 pages) and extract all headings."
- "Fetch the product listing page at this URL and return the raw HTML so I can parse the prices."
- "Use Scrapy to retrieve the robots.txt from https://example.com and show me its disallow rules."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/scrapy-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8526:8526 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8526 \
  hackerdogs/scrapy-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "scrapy-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/scrapy-mcp:latest"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

### HTTP mode (streamable-http)

First, start the server using Docker Compose or `docker run` with HTTP mode (see [Deploy](#deploy) above), then point your MCP client at the running server:

```json
{
  "mcpServers": {
    "scrapy-mcp": {
      "url": "http://localhost:8526/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8526` | HTTP port (only used with `streamable-http`) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name (e.g. "nuclei", "naabu", "julius").
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly (e.g. *"Use naabu to scan example.com"*). If you don't specify, Hackerdogs will automatically choose the best tool for the job — it may choose this one on its own.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/scrapy-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name scrapy-mcp-test -p 8526:8526 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/scrapy-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8526/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8526/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8526/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"scrapy_crawl","arguments":{"arguments":"--help"}}}'
```

**4. Clean up:**

```bash
docker stop scrapy-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the Scrapy CLI in the same container by overriding the entrypoint without starting the MCP server.

**Show help:**

```bash
docker run -i --rm --entrypoint scrapy hackerdogs/scrapy-mcp:latest --help
```
