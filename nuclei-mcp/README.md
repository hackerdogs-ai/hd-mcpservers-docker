# Nuclei MCP Server

Hackerdogs MCP wrapper for Nuclei — run vulnerability templates. No Minibridge; stdio + streamable-http via FastMCP.

## Tools

- **`run_nuclei`** — Run the CLI with arguments (e.g. `-h` for help).

## Docker

- **Stdio:** `docker run -i --rm hackerdogs/nuclei-mcpatest`
- **HTTP:** `docker run -d -p 8391:8391 -e MCP_TRANSPORT=streamable-http hackerdogs/nuclei-mcpatest` → `http://localhost:8391/mcp/`

## mcpServer.json

```json
{
  "mcpServers": {
    "nuclei-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "-e", "MCP_TRANSPORT", "-e", "MCP_PORT", "hackerdogs/nuclei-mcpatest"],
      "env": { "MCP_TRANSPORT": "stdio", "MCP_PORT": "8391" }
    }
  }
}
```
