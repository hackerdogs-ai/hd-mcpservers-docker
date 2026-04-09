<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Crunchbase MCP Server

A Model Context Protocol (MCP) server that connects AI assistants to Crunchbase data. It enables users to search for companies

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/crunchbase-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name crunchbase-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8411 \
  -p 8411:8411 \
  hackerdogs/crunchbase-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "crunchbase-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/crunchbase-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8411` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/crunchbase-mcp:latest .
```

## Test

```bash
./test.sh
```
