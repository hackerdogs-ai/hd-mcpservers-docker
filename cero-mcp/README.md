# Cero MCP Server

Hackerdogs MCP wrapper for Cero — find forgotten secrets in Git repos. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_cero`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/cero-mcp:latest`
- **HTTP:** `docker run -d -p 8396:8396 -e MCP_TRANSPORT=streamable-http hackerdogs/cero-mcp:latest` → `http://localhost:8396/mcp`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "cero-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/cero-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8396:8396 -e MCP_TRANSPORT=streamable-http hackerdogs/cero-mcp:latest
```

```json
{
  "mcpServers": {
    "cero-mcp": {
      "url": "http://localhost:8396/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
