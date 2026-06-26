# Nmap MCP Server

Hackerdogs MCP wrapper for Nmap — network discovery and port scan. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_nmap`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/nmap-mcpatest`
- **HTTP:** `docker run -d -p 8390:8390 -e MCP_TRANSPORT=streamable-http hackerdogs/nmap-mcpatest` → `http://localhost:8390/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "nmap-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/nmap-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8390:8390 -e MCP_TRANSPORT=streamable-http hackerdogs/nmap-mcp:latest
```

```json
{
  "mcpServers": {
    "nmap-mcp": {
      "url": "http://localhost:8390/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
