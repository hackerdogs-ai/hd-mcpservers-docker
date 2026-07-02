<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
    <br/>
    <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=20&duration=1&pause=10000000&color=000000&center=true&vCenter=true&repeat=false&width=180&height=28&lines=hackerdogs" alt="hackerdogs"/>
  </a>
</p>

# PageSpeed MCP Server

MCP server wrapper for [Google PageSpeed Insights](https://developers.google.com/speed/docs/insights/v5/about) — web performance and Core Web Vitals analysis via the PageSpeed Insights API v5.

## What is PageSpeed?

Google PageSpeed Insights analyzes a URL for performance, accessibility, SEO, and best-practices using Lighthouse and real-world Chrome User Experience Report (CrUX) data. This MCP server calls the PageSpeed Insights API v5 directly, supporting both mobile and desktop strategies and all four Lighthouse audit categories. An optional `PAGESPEED_API_KEY` raises the quota limit for high-volume usage.

**API key optional** — the PageSpeed Insights API works without a key at lower rate limits; set `PAGESPEED_API_KEY` for higher quota (free at [Google Cloud Console](https://console.developers.google.com/)).

**Tools:**
- `run_pagespeed` — Run PageSpeed Insights on a URL (mobile or desktop strategy, configurable categories).

## Tools Reference

### `run_pagespeed`

Run Google PageSpeed Insights on a URL and return the full Lighthouse report.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string | Yes | — | URL to analyze (must include scheme, e.g. `https://example.com`) |
| `strategy` | string | No | `mobile` | `mobile` or `desktop` |
| `categories` | string | No | all | Comma-separated: `PERFORMANCE,ACCESSIBILITY,SEO,BEST_PRACTICES` |

## Example Prompts

Here are example prompts you can use with Claude (or any MCP client) when this tool is connected:

- "Run PageSpeed Insights on https://example.com for mobile and summarize the performance score."
- "Check the desktop performance of https://myshop.com and list the top 3 opportunities to improve load time."
- "Analyze https://blog.example.com for both SEO and accessibility issues on mobile."
- "What is the Largest Contentful Paint for https://news.example.com on desktop?"
- "Run a full PageSpeed audit on https://app.example.com and identify any Core Web Vitals failures."
- "Compare mobile vs desktop performance scores for https://example.com and explain the differences."

## Deploy

### Docker Compose (recommended)

```bash
docker-compose up -d
```

### Docker Run (stdio mode)

```bash
docker run -i --rm hackerdogs/pagespeed-mcp:latest
```

### Docker Run (HTTP streamable mode)

```bash
docker run -d -p 8378:8378 \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8378 \
  hackerdogs/pagespeed-mcp:latest
```

## MCP Client Configuration

### Stdio mode (default)

Add to your Claude Desktop or Cursor MCP config:

```json
{
  "mcpServers": {
    "pagespeed-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/pagespeed-mcp:latest"],
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
    "pagespeed-mcp": {
      "url": "http://localhost:8378/mcp"
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
    "pagespeed-mcp": {
      "url": "http://localhost:8485/pagespeed-mcp/mcp",
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
| `MCP_PORT` | `8378` | HTTP port (only used with `streamable-http`) |
| `PAGESPEED_API_KEY` | `` | Google PageSpeed Insights API key (optional, raises quota) |

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
docker build -t hackerdogs/pagespeed-mcp:latest .
```

## Testing

### Automated tests

```bash
./test.sh
```

### Test directly with Docker

**1. Start the server in HTTP mode:**

```bash
docker run -d --rm --name pagespeed-mcp-test -p 8378:8378 \
  -e MCP_TRANSPORT=streamable-http \
  hackerdogs/pagespeed-mcp:latest
```

**2. Initialize the MCP session:**

```bash
SESSION_ID=$(curl -s -D - -X POST http://localhost:8378/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"0.1"}}}' \
  2>&1 | grep -i mcp-session-id | awk '{print $2}' | tr -d '\r\n')

curl -s -X POST http://localhost:8378/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
```

**3. Call a tool:**

```bash
curl -s -X POST http://localhost:8378/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "mcp-session-id: $SESSION_ID" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"run_pagespeed","arguments":{"url":"https://example.com","strategy":"mobile"}}}'
```

**4. Clean up:**

```bash
docker stop pagespeed-mcp-test
```

## Running the tool directly (bypassing MCP)

You can run the PageSpeed MCP server in the same container by overriding the entrypoint without starting the MCP wrapper.

**Show help:**

```bash
docker run -i --rm --entrypoint python hackerdogs/pagespeed-mcp:latest mcp_server.py --help
```
