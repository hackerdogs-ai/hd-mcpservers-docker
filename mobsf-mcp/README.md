# MobSF MCP Server

Hackerdogs MCP wrapper for MobSF — analyze mobile apps (tool install TBD). No Minibridge; stdio + streamable-http via FastMCP. Tool install is TBD.

## Tools

- **`run_mobsf`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/mobsf-mcpatest`
- **HTTP:** `docker run -d -p 8389:8389 -e MCP_TRANSPORT=streamable-http hackerdogs/mobsf-mcpatest` → `http://localhost:8389/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "mobsf-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/mobsf-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8389:8389 -e MCP_TRANSPORT=streamable-http hackerdogs/mobsf-mcp:latest
```

```json
{
  "mcpServers": {
    "mobsf-mcp": {
      "url": "http://localhost:8389/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
