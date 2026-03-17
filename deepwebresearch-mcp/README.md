# Deep Web Research MCP Server

Fetch URLs and extract text for research. Use one URL or multiple; optional character limit per response.

- **Port:** 8377 (streamable-http)
- **Env:** `MCP_TRANSPORT`, `MCP_PORT`

## Tools

| Tool | Description |
|------|-------------|
| `fetch_url` | Fetch one URL; return extracted text and metadata. Optional `max_chars` (default 50000). |
| `fetch_urls` | Fetch multiple URLs (comma- or newline-separated). Optional `max_chars_per_url` (default 20000). Max 20 URLs per call. |

## Docker Run (stdio)

```bash
docker run -i --rm -e MCP_TRANSPORT=stdio hackerdogs/deepwebresearch-mcp:latest
```

## Docker Run (HTTP streamable)

```bash
docker run -d -p 8377:8377 -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8377 hackerdogs/deepwebresearch-mcp:latest
```
