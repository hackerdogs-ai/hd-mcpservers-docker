# prowler-mcp

> Prowler — remote streamable-HTTP endpoint (no local build needed).

## Description

Prowler MCP Server — cloud security posture assessment for AWS, Azure, GCP, and Kubernetes.

## Category

OSS

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://mcp.prowler.com/mcp` |

## Setup

1. Sign up at [Prowler](https://prowler.com) and configure cloud credentials as needed.
2. Add the `mcpServer.json` config to your MCP client.

## License

Open source — see [Prowler](https://prowler.com) for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "prowler-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/prowler-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8515:8515 -e MCP_TRANSPORT=streamable-http hackerdogs/prowler-mcp:latest
```

```json
{
  "mcpServers": {
    "prowler-mcp": {
      "url": "http://localhost:8515/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
