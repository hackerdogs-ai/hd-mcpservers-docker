<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# Bright Data MCP Server

MCP server wrapper for [Bright Data](https://github.com/brightdata/brightdata-mcp) — scalable web scraping and data collection with built-in proxy infrastructure and bot bypass.

## What is Bright Data?

Bright Data is a web data platform offering managed proxy infrastructure, browser APIs, and scraping tools that bypass bot detection, CAPTCHAs, and geo-restrictions at scale. This server wraps the official `@brightdata/mcp` package to expose Bright Data's scraping and data collection capabilities — including the Scraping Browser, SERP API, and Web Unlocker — to any MCP client. See [github.com/brightdata/brightdata-mcp](https://github.com/brightdata/brightdata-mcp) for full documentation.

**API token required** — sign up at [brightdata.com](https://brightdata.com/) and set `API_TOKEN`.

## Tools Reference

| Tool | Description |
|------|-------------|
| `search_engine` | Search Engine |
| `scrape_as_markdown` | Scrape As Markdown |
| `search_engine_batch` | Search Engine Batch |
| `scrape_batch` | Scrape Batch |
| `discover` | Discover |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Use Bright Data to scrape the product listings page at example-shop.com and return structured data."
- "Fetch the JavaScript-rendered content of a React SPA at app.example.com using Bright Data's browser API."
- "Collect Google SERP results for 'best VPN 2026' using Bright Data's SERP API."
- "Use Bright Data to access geo-restricted content from a US IP address."
- "Scrape competitor pricing from multiple e-commerce pages without getting blocked."
- "Extract job listings from a site that blocks regular HTTP requests using Bright Data Web Unlocker."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm \
  -e API_TOKEN \
  hackerdogs/brightdata-mcp-server-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8630:8630 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8630 \
  -e API_TOKEN \
  hackerdogs/brightdata-mcp-server-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "brightdata-mcp-server-mcp": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "MCP_TRANSPORT",
        "-e",
        "API_TOKEN",
        "hackerdogs/brightdata-mcp-server-mcp:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "API_TOKEN": ""
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
    "brightdata-mcp-server-mcp": {
      "url": "http://localhost:8630/mcp"
    }
  }
}
```

> **When to use HTTP mode:** HTTP mode is ideal for shared/remote deployments, multi-user setups, and [Hackerdogs](https://hackerdogs.ai) scheduled prompts. The server runs as a long-lived process and accepts connections from multiple MCP clients concurrently.


## Securely Accessing MCP

When running through the [Hackerdogs MCP Farm](https://hackerdogs.ai), servers are accessed through the authenticated gateway instead of direct container ports:

```json
{
  "mcpServers": {
    "brightdata-mcp-server-mcp": {
      "url": "http://localhost:8485/brightdata-mcp-server-mcp/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-key>"
      }
    }
  }
}
```

> **Farm access:** The MCP Farm gateway handles authentication, rate limiting, and routing. Replace `localhost:8485` with your farm's host address and use your API key from the farm admin panel. See [Hackerdogs](https://hackerdogs.ai) for details.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport mode: `stdio` or `streamable-http` |
| `MCP_PORT` | `8630` | HTTP port (only used with `streamable-http`) |
| `API_TOKEN` | — | Bright Data API token |
| `BRIGHTDATA_API_TOKEN` | — | Bright Data API token (required) |

## Installing in Hackerdogs

The fastest way to get started is through [Hackerdogs](https://hackerdogs.ai):

1. **Log in** to your Hackerdogs account.
2. Go to the **Tools Catalog**.
3. **Search** for the tool by name.
4. Expand the tool card and click **Install** — you're ready to go.

> Give it a couple of minutes to go live. Then start querying by asking Hackerdogs to use the tool explicitly. If you don't specify, Hackerdogs will automatically choose the best tool for the job.

5. **Vendor API key required?** Add your key in the config environment variable field before clicking Install. Your key will be encrypted at rest.
6. **Enable / Disable** the tool anytime from the **Enabled Tools** page.
7. **Need to update a key or parameter?** Go to **My Tools** → toggle **Show Decrypted Values** → edit → **Save**.

> **Want to contribute or chat with the team?** Join our [Discord](https://discord.gg/str9FcWuyM).

## Build

```bash
docker build -t hackerdogs/brightdata-mcp-server-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name brightdata-mcp-server-mcp-test -p 8630:8630 \
  -e MCP_TRANSPORT=streamable-http \
  -e API_TOKEN \
  hackerdogs/brightdata-mcp-server-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8630/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8630/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. List available tools:**

```bash
curl -s -X POST http://localhost:8630/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

**4. Clean up:**

```bash
docker stop brightdata-mcp-server-mcp-test
```
