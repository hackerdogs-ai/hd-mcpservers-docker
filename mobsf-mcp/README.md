# MobSF MCP Server

Hackerdogs MCP wrapper for MobSF — analyze mobile apps (tool install TBD). No Minibridge; stdio + streamable-http via FastMCP. Tool install is TBD.

## Tools

- **`run_mobsf`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/mobsf-mcpatest`
- **HTTP:** `docker run -d -p 8389:8389 -e MCP_TRANSPORT=streamable-http hackerdogs/mobsf-mcpatest` → `http://localhost:8389/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "mobsf-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/mobsf-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8389" }
    }
  }
}
```
