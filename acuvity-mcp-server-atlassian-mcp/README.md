<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Atlassian MCP Server

Integrates AI tools for Jira and Confluence tasks and automation. Model Context Protocol (MCP) server for Atlassian products (Confluence and

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-atlassian-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-atlassian-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8404 \
  -p 8404:8404 \
  hackerdogs/acuvity-mcp-server-atlassian-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-atlassian-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-atlassian-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8404` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-atlassian-mcp:latest .
```

## Test

```bash
./test.sh
```
