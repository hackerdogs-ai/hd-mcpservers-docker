# mitre-attack-remote-mcp

> MITRE ATT&CK — remote streamable-HTTP endpoint (no local build needed).

## Description

MITRE ATT&CK MCP Server wrapping the MITRE Python SDK. Query techniques, tactics, mitigations, and groups.

## Category

Hybrid

## Connection

This is a **remote-only** MCP server. No Docker image or local build is required.

| Transport | URL |
|-----------|-----|
| Streamable HTTP | `https://attack-mcp.mitre.org/mcp` |

## Setup

1. Configure the server URL in your MCP client.
2. Add the `mcpServer.json` config to your MCP client.

## License

MITRE ATT&CK® is licensed under CC-BY 4.0 — see [MITRE](https://attack.mitre.org) for terms.

## mcpServer.json

### Stdio (local / Cursor / Claude Desktop)

```json
{
  "mcpServers": {
    "mitre-attack-remote-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/mitre-attack-remote-mcp:latest"],
      "env": {}
    }
  }
}
```

### Streamable HTTP (remote / farm / multi-client)

```bash
docker run -d -p 8516:8516 -e MCP_TRANSPORT=streamable-http hackerdogs/mitre-attack-remote-mcp:latest
```

```json
{
  "mcpServers": {
    "mitre-attack-remote-mcp": {
      "url": "http://localhost:8516/mcp/",
      "transport": "streamable-http"
    }
  }
}
```
