# Arjun MCP Server

Hackerdogs MCP wrapper for [Arjun](https://github.com/s0md3v/Arjun) — discover hidden HTTP parameters. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`do_arjun`** — Run Arjun with CLI arguments (e.g. `-u https://example.com`).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/arjun-mcp:latest`
- **HTTP:** `docker run -d -p 8383:8383 -e MCP_TRANSPORT=streamable-http hackerdogs/arjun-mcp:latest` → `http://localhost:8383/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "arjun-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/arjun-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8383:8383 -e MCP_TRANSPORT=streamable-http hackerdogs/arjun-mcp:latest
```

```json
{
  "mcpServers": {
    "arjun-mcp": {
      "url": "http://localhost:8383/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
