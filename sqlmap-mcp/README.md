# Sqlmap MCP Server

Hackerdogs MCP wrapper for Sqlmap — detect and exploit SQL injection. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_sqlmap`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/sqlmap-mcpatest`
- **HTTP:** `docker run -d -p 8394:8394 -e MCP_TRANSPORT=streamable-http hackerdogs/sqlmap-mcpatest` → `http://localhost:8394/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "sqlmap-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/sqlmap-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8394" }
    }
  }
}
```
