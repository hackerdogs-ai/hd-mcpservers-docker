# PageSpeed MCP Server

Google **PageSpeed Insights** (v5) for a URL. Returns performance, accessibility, SEO, and best-practices metrics.

- **Port:** 8378 (streamable-http)
- **Env:** `MCP_TRANSPORT`, `MCP_PORT`, `PAGESPEED_API_KEY` (optional; recommended for higher quota)

## Tools

| Tool | Description |
|------|-------------|
| `run_pagespeed` | Run PageSpeed on a URL. Args: `url`, `strategy` (mobile/desktop), optional `categories`. |

## Docker Run (stdio)

```bash
docker run -i --rm -e MCP_TRANSPORT=stdio hackerdogs/pagespeed-mcp:latest
```

With API key (recommended):

```bash
docker run -i --rm -e MCP_TRANSPORT=stdio -e PAGESPEED_API_KEY=your_key hackerdogs/pagespeed-mcp:latest
```

## Docker Run (HTTP streamable)

```bash
docker run -d -p 8378:8378 -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8378 -e PAGESPEED_API_KEY=your_key hackerdogs/pagespeed-mcp:latest
```

API key: [Google Cloud Console](https://console.cloud.google.com/) → enable PageSpeed Insights API.
