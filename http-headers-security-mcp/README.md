# HTTP Headers Security MCP Server

Hackerdogs MCP wrapper for HTTP Headers Security — check HTTP security headers (tool install TBD). No Minibridge; stdio + streamable-http via FastMCP. Tool install is TBD.

## Tools

- **`run_http_headers_security`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/http-headers-security-mcpatest`
- **HTTP:** `docker run -d -p 8392:8392 -e MCP_TRANSPORT=streamable-http hackerdogs/http-headers-security-mcpatest` → `http://localhost:8392/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "http-headers-security-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/http-headers-security-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8392" }
    }
  }
}
```
