# Shuffledns MCP Server

Hackerdogs MCP wrapper for Shuffledns — resolve and enumerate subdomains via DNS. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_shuffledns`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/shuffledns-mcpatest`
- **HTTP:** `docker run -d -p 8393:8393 -e MCP_TRANSPORT=streamable-http hackerdogs/shuffledns-mcpatest` → `http://localhost:8393/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "shuffledns-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/shuffledns-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8393" }
    }
  }
}
```
