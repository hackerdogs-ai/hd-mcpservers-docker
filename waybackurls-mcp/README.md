# Waybackurls MCP Server

Hackerdogs MCP wrapper for Waybackurls — fetch historical URLs from Wayback Machine. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_waybackurls`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/waybackurls-mcpatest`
- **HTTP:** `docker run -d -p 8395:8395 -e MCP_TRANSPORT=streamable-http hackerdogs/waybackurls-mcpatest` → `http://localhost:8395/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "waybackurls-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/waybackurls-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8395:8395 -e MCP_TRANSPORT=streamable-http hackerdogs/waybackurls-mcp:latest
```

```json
{
  "mcpServers": {
    "waybackurls-mcp": {
      "url": "http://localhost:8395/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
