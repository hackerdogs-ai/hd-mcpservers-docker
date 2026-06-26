<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Alterx MCP Server

MCP server for **Alterx** — domain wordlist generation (subdomain permutation). Wraps the Acuvity/Alterx image for use in MCP-compatible applications and AI workflows.

**Upstream:** [acuvity/mcp-server-alterx](https://hub.docker.com/r/acuvity/mcp-server-alterx) · [GitHub (cyproxio/mcp-for-security)](https://github.com/cyproxio/mcp-for-security/tree/HEAD/alterx-mcp)

## Docker Run (stdio)

```bash
docker run -i --rm acuvity/mcp-server-alterx:latest
```

## Env / Port

- Default: stdio transport. If the image supports HTTP streamable, use port **8380** and set `MCP_TRANSPORT=streamable-http`, `MCP_PORT=8380`.

## Tools

Exposes Alterx domain wordlist generation for subdomain enumeration and discovery workflows.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-alterx-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-alterx-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8380:8380 -e MCP_TRANSPORT=streamable-http hackerdogs/acuvity-mcp-server-alterx-mcp:latest
```

```json
{
  "mcpServers": {
    "acuvity-mcp-server-alterx-mcp": {
      "url": "http://localhost:8380/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
