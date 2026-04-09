# BuiltWith MCP Server

Domain technology stack lookup via the **BuiltWith Domain API** (v22). Returns technologies, paths, and metadata for a given domain.

- **Port:** 8375 (streamable-http)
- **Env:** `MCP_TRANSPORT`, `MCP_PORT`, `BUILTWITH_API_KEY` (required)

## Tools

| Tool | Description |
|------|-------------|
| `domain_lookup` | Get technology stack for a domain (e.g. `example.com`). Returns BuiltWith JSON. |

## Docker Run (stdio)

```bash
docker run -i --rm -e MCP_TRANSPORT=stdio -e BUILTWITH_API_KEY=your_key hackerdogs/builtwith-mcp:latest
```

## Docker Run (HTTP streamable)

```bash
docker run -d -p 8375:8375 -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8375 -e BUILTWITH_API_KEY=your_key hackerdogs/builtwith-mcp:latest
```

Get an API key at [BuiltWith](https://builtwith.com/).
