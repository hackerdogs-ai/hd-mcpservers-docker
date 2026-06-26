# Nuclei MCP Server

Hackerdogs MCP wrapper for Nuclei — run vulnerability templates. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_nuclei`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/nuclei-mcpatest`
- **HTTP:** `docker run -d -p 8391:8391 -e MCP_TRANSPORT=streamable-http hackerdogs/nuclei-mcpatest` → `http://localhost:8391/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "nuclei-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/nuclei-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8391:8391 -e MCP_TRANSPORT=streamable-http hackerdogs/nuclei-mcp:latest
```

```json
{
  "mcpServers": {
    "nuclei-mcp": {
      "url": "http://localhost:8391/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
