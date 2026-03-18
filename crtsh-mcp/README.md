# crt.sh MCP Server

<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

MCP server for subdomain discovery from SSL certificate logs via [crt.sh](https://crt.sh). **Hackerdogs build: stdio + streamable-http via FastMCP only (no Minibridge).** No local binary; uses the crt.sh JSON API.

## Tools

- **`crtsh`** — Query crt.sh for subdomains of a given domain.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target` | string | Yes | Target domain (e.g. example.com) |

## Docker

**Stdio:** `docker run -i --rm hackerdogs/crtsh-mcp:latest`  
**Streamable HTTP:** `docker run -d -p 8381:8381 -e MCP_TRANSPORT=streamable-http hackerdogs/crtsh-mcp:latest` → `http://localhost:8381/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "crtsh-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "hackerdogs/crtsh-mcp:latest"],
      "env": { "MCP_TRANSPORT": "stdio" }
    }
  }
}
```
