# Masscan MCP Server

Hackerdogs MCP wrapper for Masscan — scan ports at scale. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_masscan`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/masscan-mcpatest`
- **HTTP:** `docker run -d -p 8388:8388 -e MCP_TRANSPORT=streamable-http hackerdogs/masscan-mcpatest` → `http://localhost:8388/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "masscan-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/masscan-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8388:8388 -e MCP_TRANSPORT=streamable-http hackerdogs/masscan-mcp:latest
```

```json
{
  "mcpServers": {
    "masscan-mcp": {
      "url": "http://localhost:8388/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
