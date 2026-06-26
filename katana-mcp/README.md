# Katana MCP Server

Hackerdogs MCP wrapper for Katana — crawl and discover URLs. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_katana`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/katana-mcpatest`
- **HTTP:** `docker run -d -p 8387:8387 -e MCP_TRANSPORT=streamable-http hackerdogs/katana-mcpatest` → `http://localhost:8387/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "katana-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/katana-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8387:8387 -e MCP_TRANSPORT=streamable-http hackerdogs/katana-mcp:latest
```

```json
{
  "mcpServers": {
    "katana-mcp": {
      "url": "http://localhost:8387/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
