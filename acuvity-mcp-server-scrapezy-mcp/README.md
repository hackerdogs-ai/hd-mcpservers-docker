<p align="center">
  <a href="https://hackerdogs.ai">
    <img src="https://hackerdogs.ai/images/logo.png" alt="Hackerdogs" width="120"/>
  </a>
</p>

# Scrapezy MCP Server

A Model Context Protocol server for Scrapezy that enables AI models to extract structured data from websites.  Features Tools extract_struct

## Docker Run (stdio)

```bash
docker run -i --rm hackerdogs/acuvity-mcp-server-scrapezy-mcp:latest
```

## Docker Run (HTTP streamable mode)

```bash
docker run -d --name acuvity-mcp-server-scrapezy-mcp \
  -e MCP_TRANSPORT=streamable-http \
  -e MCP_PORT=8450 \
  -p 8450:8450 \
  hackerdogs/acuvity-mcp-server-scrapezy-mcp:latest
```

## MCP Client Configuration (stdio)

```json
{
  "mcpServers": {
    "acuvity-mcp-server-scrapezy-mcp": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/acuvity-mcp-server-scrapezy-mcp:latest"]
    }
  }
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` or `streamable-http` |
| `MCP_PORT` | `8450` | HTTP port (streamable-http mode) |

## Build

```bash
docker build -t hackerdogs/acuvity-mcp-server-scrapezy-mcp:latest .
```

## Test

```bash
./test.sh
```
