# Ffuf MCP Server

Hackerdogs MCP wrapper for Ffuf — fuzz HTTP endpoints. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_ffuf`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/ffuf-mcpatest`
- **HTTP:** `docker run -d -p 8385:8385 -e MCP_TRANSPORT=streamable-http hackerdogs/ffuf-mcpatest` → `http://localhost:8385/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "ffuf-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/ffuf-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8385:8385 -e MCP_TRANSPORT=streamable-http hackerdogs/ffuf-mcp:latest
```

```json
{
  "mcpServers": {
    "ffuf-mcp": {
      "url": "http://localhost:8385/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
