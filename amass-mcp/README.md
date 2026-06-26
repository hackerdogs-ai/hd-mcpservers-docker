# Amass MCP Server

Hackerdogs MCP wrapper for [OWASP Amass](https://github.com/owasp-amass/amass) — subdomain enumeration and reconnaissance. **No Minibridge;** stdio + streamable-http via FastMCP.

## Tools

- **`run_amass`** — Run amass with CLI arguments (e.g. `enum -d example.com`, `intel -d example.com -whois`).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/amass-mcp:latest`
- **HTTP:** `docker run -d -p 8382:8382 -e MCP_TRANSPORT=streamable-http hackerdogs/amass-mcp:latest` → `http://localhost:8382/mcp/`

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "amass-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/amass-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8382:8382 -e MCP_TRANSPORT=streamable-http hackerdogs/amass-mcp:latest
```

```json
{
  "mcpServers": {
    "amass-mcp": {
      "url": "http://localhost:8382/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
