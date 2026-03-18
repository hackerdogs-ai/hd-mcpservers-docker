# Gowitness MCP Server

Hackerdogs MCP wrapper for Gowitness — take screenshots of web targets. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_gowitness`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/gowitness-mcpatest`
- **HTTP:** `docker run -d -p 8397:8397 -e MCP_TRANSPORT=streamable-http hackerdogs/gowitness-mcpatest` → `http://localhost:8397/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "gowitness-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/gowitness-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8397" }
    }
  }
}
```
