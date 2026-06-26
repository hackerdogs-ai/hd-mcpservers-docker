# Shuffledns MCP Server

Hackerdogs MCP wrapper for Shuffledns — resolve and enumerate subdomains via DNS. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_shuffledns`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/shuffledns-mcpatest`
- **HTTP:** `docker run -d -p 8393:8393 -e MCP_TRANSPORT=streamable-http hackerdogs/shuffledns-mcpatest` → `http://localhost:8393/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "shuffledns-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/shuffledns-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8393:8393 -e MCP_TRANSPORT=streamable-http hackerdogs/shuffledns-mcp:latest
```

```json
{
  "mcpServers": {
    "shuffledns-mcp": {
      "url": "http://localhost:8393/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
