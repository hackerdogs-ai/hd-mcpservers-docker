# Assetfinder MCP Server

Hackerdogs MCP wrapper for Assetfinder — find related domains. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_assetfinder`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/assetfinder-mcpatest`
- **HTTP:** `docker run -d -p 8384:8384 -e MCP_TRANSPORT=streamable-http hackerdogs/assetfinder-mcpatest` → `http://localhost:8384/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "assetfinder-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/assetfinder-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8384:8384 -e MCP_TRANSPORT=streamable-http hackerdogs/assetfinder-mcp:latest
```

```json
{
  "mcpServers": {
    "assetfinder-mcp": {
      "url": "http://localhost:8384/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
