# Code Execution MCP Server

Run **Python code** in a sandboxed subprocess. Returns stdout, stderr, and exit code. No network; only a temp dir is writable. Safe for untrusted snippet execution.

- **Port:** 8376 (streamable-http)
- **Env:** `MCP_TRANSPORT`, `MCP_PORT`

## Tools

| Tool | Description |
|------|-------------|
| `run_python` | Execute Python code. Args: `code`, optional `timeout_seconds` (default 30, max 120). |

## Docker Run (stdio)

```bash
docker run -i --rm -e MCP_TRANSPORT=stdio hackerdogs/code-execution-mcp:latest
```

## Docker Run (HTTP streamable)

```bash
docker run -d -p 8376:8376 -e MCP_TRANSPORT=streamable-http -e MCP_PORT=8376 hackerdogs/code-execution-mcp:latest
```

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "code-execution-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/code-execution-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8376:8376 -e MCP_TRANSPORT=streamable-http hackerdogs/code-execution-mcp:latest
```

```json
{
  "mcpServers": {
    "code-execution-mcp": {
      "url": "http://localhost:8376/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
