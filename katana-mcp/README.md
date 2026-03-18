# Katana MCP Server

Hackerdogs MCP wrapper for Katana — crawl and discover URLs. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_katana`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/katana-mcpatest`
- **HTTP:** `docker run -d -p 8387:8387 -e MCP_TRANSPORT=streamable-http hackerdogs/katana-mcpatest` → `http://localhost:8387/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "katana-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/katana-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8387" }
    }
  }
}
```
