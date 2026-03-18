# Httpx MCP Server

Hackerdogs MCP wrapper for Httpx — probe and analyze HTTP servers. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_httpx`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/httpx-mcpatest`
- **HTTP:** `docker run -d -p 8386:8386 -e MCP_TRANSPORT=streamable-http hackerdogs/httpx-mcpatest` → `http://localhost:8386/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "httpx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/httpx-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8386" }
    }
  }
}
```
