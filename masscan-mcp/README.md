# Masscan MCP Server

Hackerdogs MCP wrapper for Masscan — scan ports at scale. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_masscan`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/masscan-mcpatest`
- **HTTP:** `docker run -d -p 8388:8388 -e MCP_TRANSPORT=streamable-http hackerdogs/masscan-mcpatest` → `http://localhost:8388/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "masscan-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/masscan-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8388" }
    }
  }
}
```
