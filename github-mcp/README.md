# github-mcp

> GitHub MCP Server — remote streamable-HTTP endpoint (no local build needed).

## Description

Connects AI tools to GitHub's platform for reading repos, managing issues/PRs, and code search.

## Category

OSS

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://api.githubcopilot.com/mcp/` |

## Setup

1. Obtain a GitHub token and configure it in your MCP client.
2. Add the `mcpServer.json` config to your MCP client.

## License

Open source — see [GitHub](https://github.com) for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "github-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/github-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8521:8521 -e MCP_TRANSPORT=streamable-http hackerdogs/github-mcp:latest
```

```json
{
  "mcpServers": {
    "github-mcp": {
      "url": "http://localhost:8521/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
