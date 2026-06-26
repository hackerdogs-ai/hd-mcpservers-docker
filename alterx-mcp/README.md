# Alterx MCP Server

<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

MCP server wrapper for [Alterx](https://github.com/projectdiscovery/alterx) — pattern-based wordlist generator for subdomain discovery. **Hackerdogs build: stdio + streamable-http via FastMCP only (no Minibridge).**

## Tools

- **`do_alterx`** — Run alterx with domain and pattern; optional output file path.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `domain` | string | Yes | Target domain(s), comma-separated or single |
| `pattern` | string | Yes | Pattern template (e.g. `{{word}}-{{sub}}.{{suffix}}`) |
| `output_file_path` | string | No | Path to save wordlist (optional) |
| `timeout_seconds` | int | No | Max execution time (default 120) |

## Docker

**Stdio:**
```bash
docker run -i --rm hackerdogs/alterx-mcp:latest
```

**Streamable HTTP:**
```bash
docker run -d -p 8380:8380 -e MCP_TRANSPORT=streamable-http hackerdogs/alterx-mcp:latest
# Endpoint: http://localhost:8380/mcp/
```

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "alterx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/alterx-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8380:8380 -e MCP_TRANSPORT=streamable-http hackerdogs/alterx-mcp:latest
```

```json
{
  "mcpServers": {
    "alterx-mcp": {
      "url": "http://localhost:8380/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
