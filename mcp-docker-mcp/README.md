# mcp-docker-mcp

> Docker MCP Toolkit Gateway — remote streamable-HTTP endpoint (no local build needed).

## Description

An aggregator and gateway for containerized MCP servers. Provides a single entry point to a catalog of MCP tools.

## Category

OSS

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.docker.com/mcp` |

## Setup

1. Configure the server URL in your MCP client.
2. Add the `mcpServer.json` config to your MCP client.

## License

Open source — see Docker for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "mcp-docker-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/mcp-docker-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8517:8517 -e MCP_TRANSPORT=streamable-http hackerdogs/mcp-docker-mcp:latest
```

```json
{
  "mcpServers": {
    "mcp-docker-mcp": {
      "url": "http://localhost:8517/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
